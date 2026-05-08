import os

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def create_database_if_missing():
    """Connect to the default 'postgres' DB and create the target DB if it doesn't exist."""
    from urllib.parse import urlparse
    url = urlparse(DATABASE_URL)
    db_name = url.path.lstrip("/")
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"Database '{db_name}' created.")
    finally:
        conn.close()

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()


def init_db():
    """Create all tables that are defined in models (safe to call on startup)."""
    import backend.models  # noqa: F401 — registers ORM models with Base
    Base.metadata.create_all(bind=engine)
    _migrate_user_trips()
    _migrate_reviews()
    _migrate_trip_completions()
    _migrate_landmark_images()


def _migrate_user_trips():
    """Add columns introduced after initial schema creation (idempotent)."""
    migrations = [
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS current_point_index INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS visited_indices JSON NOT NULL DEFAULT '[]'",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS route_legs JSON NOT NULL DEFAULT '[]'",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS custom_start_location JSON",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS custom_end_location JSON",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS saved_user_location JSON",
        "ALTER TABLE user_trips ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT FALSE",
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_trips' AND column_name = 'user_location_start'
            ) THEN
                UPDATE user_trips
                SET custom_start_location = user_location_start
                WHERE custom_start_location IS NULL AND user_location_start IS NOT NULL;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_trips' AND column_name = 'user_location_end'
            ) THEN
                UPDATE user_trips
                SET custom_end_location = user_location_end
                WHERE custom_end_location IS NULL AND user_location_end IS NOT NULL;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_trips' AND column_name = 'user_location_start'
            ) THEN
                UPDATE user_trips
                SET saved_user_location = user_location_start
                WHERE saved_user_location IS NULL
                  AND user_location_start IS NOT NULL;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_trips' AND column_name = 'user_location_end'
            ) THEN
                UPDATE user_trips
                SET saved_user_location = user_location_end
                WHERE saved_user_location IS NULL
                  AND user_location_end IS NOT NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS user_location_start",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS user_location_end",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS used_user_location_start",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS used_user_location_end",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS saved_start_lat",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS saved_start_lon",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS saved_end_lat",
        "ALTER TABLE user_trips DROP COLUMN IF EXISTS saved_end_lon",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()


def _migrate_reviews():
    """Add columns introduced after initial reviews schema creation (idempotent)."""
    migrations = [
        "ALTER TABLE reviews ADD COLUMN IF NOT EXISTS landmark_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'reviews_landmark_id_fkey'
            ) THEN
                ALTER TABLE reviews
                ADD CONSTRAINT reviews_landmark_id_fkey
                FOREIGN KEY (landmark_id) REFERENCES landmarks(id);
            END IF;
        END $$;
        """,
        "CREATE INDEX IF NOT EXISTS ix_reviews_landmark_id ON reviews (landmark_id)",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()


def _migrate_trip_completions():
    """Normalize trip completion columns introduced after initial schema creation."""
    migrations = [
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trip_completions' AND column_name = 'revew_text'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trip_completions' AND column_name = 'review_text'
            ) THEN
                ALTER TABLE trip_completions RENAME COLUMN revew_text TO review_text;
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trip_completions' AND column_name = 'revew_text'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trip_completions' AND column_name = 'review_text'
            ) THEN
                UPDATE trip_completions
                SET review_text = COALESCE(review_text, revew_text)
                WHERE review_text IS NULL AND revew_text IS NOT NULL;

                ALTER TABLE trip_completions DROP COLUMN revew_text;
            END IF;
        END $$;
        """,
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()


def _migrate_landmark_images():
    """Add columns/indexes for cached Wikimedia image metadata."""
    migrations = [
        "ALTER TABLE landmark_images DROP COLUMN IF EXISTS wikidata_id",
        "ALTER TABLE landmark_images DROP COLUMN IF EXISTS is_primary",
        "ALTER TABLE landmark_images DROP COLUMN IF EXISTS sort_order",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS commons_file VARCHAR(500)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS image_url VARCHAR(1000)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS image_source_url VARCHAR(1000)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS author VARCHAR(500)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS license VARCHAR(200)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS license_url VARCHAR(1000)",
        "ALTER TABLE landmark_images ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP",
        "CREATE INDEX IF NOT EXISTS ix_landmark_images_landmark_id ON landmark_images (landmark_id)",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))
        conn.commit()


def shutdown_session(exception=None):
    """Remove the scoped session.  Wire to Flask's teardown_appcontext."""
    SessionLocal.remove()

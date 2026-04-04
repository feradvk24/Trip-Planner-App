import os

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
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


def shutdown_session(exception=None):
    """Remove the scoped session.  Wire to Flask's teardown_appcontext."""
    SessionLocal.remove()

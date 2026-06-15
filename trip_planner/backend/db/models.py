from sqlalchemy import Boolean, Column, Float, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from datetime import datetime, timezone

from trip_planner.backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    active_trip_id = Column(Integer, ForeignKey("user_trips.id", ondelete="SET NULL"), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    salt = Column(String(64), nullable=False)
    password = Column(String(128), nullable=False)
    role = Column(String(20), default="regular", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    verification_token_hash = Column(String(255), nullable=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    password_reset_token_hash = Column(String(255), nullable=True, index=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    location = Column(String(300), nullable=True)
    en_name = Column(String(300), nullable=True)
    en_location = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    link = Column(String(500), nullable=True)
    access_point = Column(JSON, nullable=True)  # None or {"lat": ..., "lon": ...}


class LandmarkImage(Base):
    __tablename__ = "landmark_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    landmark_id = Column(Integer, ForeignKey("landmarks.id"), nullable=False, index=True)

    commons_file = Column(String(500), nullable=True)
    image_url = Column(String(1000), nullable=True)
    image_source_url = Column(String(1000), nullable=True)

    author = Column(String(500), nullable=True)
    license = Column(String(200), nullable=True)
    license_url = Column(String(1000), nullable=True)

    fetched_at = Column(DateTime, nullable=True)


class UserTrip(Base):
    __tablename__ = "user_trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    landmark_ids = Column(JSON, nullable=False)
    visit_order = Column(JSON, nullable=False)
    route_legs = Column(JSON, default=list, nullable=False)
    custom_start_location = Column(JSON, nullable=True)  # None or {"lat": ..., "lon": ...}
    custom_end_location = Column(JSON, nullable=True)    # None or {"lat": ..., "lon": ...}
    saved_user_location = Column(JSON, nullable=True)    # None or {"lat": ..., "lon": ...}
    current_point_index = Column(Integer, default=0, nullable=False)
    visited_indices = Column(JSON, default=list, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class TripCompletion(Base):
    __tablename__ = "trip_completions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    trip_id = Column(Integer, ForeignKey("user_trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    review_text = Column(String(1000), nullable=True)


class UserLandmarkVisit(Base):
    __tablename__ = "user_landmark_visits"
    __table_args__ = (
        UniqueConstraint("user_id", "landmark_id", "trip_id", name="uq_user_landmark_trip_visit"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    landmark_id = Column(Integer, ForeignKey("landmarks.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("user_trips.id"), nullable=False, index=True)

    visited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)

    trip_id = Column(Integer, ForeignKey("user_trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    landmark_id = Column(Integer, ForeignKey("landmarks.id"), nullable=False, index=True)

    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

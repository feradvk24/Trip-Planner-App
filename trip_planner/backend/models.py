from sqlalchemy import Column, Float, Integer, String, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime, timezone

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    salt = Column(String(64), nullable=False)
    password = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    location = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    link = Column(String(500), nullable=True)


class UserTrip(Base):
    __tablename__ = "user_trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    landmark_ids = Column(JSON, nullable=False)
    visit_order = Column(JSON, nullable=False)
    used_user_location_start = Column(Boolean, default=False, nullable=False)
    used_user_location_end = Column(Boolean, default=False, nullable=False)
    current_point_index = Column(Integer, default=0, nullable=False)
    visited_indices = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

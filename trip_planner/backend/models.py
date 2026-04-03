from sqlalchemy import Column, Float, Integer, String

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    salt = Column(String(64), nullable=False)
    password = Column(String(128), nullable=False)


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    location = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    link = Column(String(500), nullable=True)

from datetime import datetime, timezone
from enum import Enum

from trip_planner.backend.db.database import SessionLocal
from trip_planner.backend.db.models import User


class EmailVerificationStatus(Enum):
    INVALID = "invalid"
    ALREADY_VERIFIED = "already"
    EXPIRED = "expired"
    SUCCESS = "success"


def get_user_email(username: str) -> str | None:
    """Return the email address for a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.email if user else None
    finally:
        db.close()


def get_user_auth_record(username: str) -> dict | None:
    """Return the fields needed to authenticate a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return {
            "username": user.username,
            "salt": user.salt,
            "password": user.password,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }
    finally:
        db.close()


def verify_user_email_token(token_hash: str) -> EmailVerificationStatus:
    """Mark a user verified if the token hash exists and has not expired."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.verification_token_hash == token_hash).first()
        if not user:
            return EmailVerificationStatus.INVALID
        if user.is_verified:
            return EmailVerificationStatus.ALREADY_VERIFIED

        expires_at = user.verification_token_expires_at
        if expires_at is None:
            return EmailVerificationStatus.INVALID
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return EmailVerificationStatus.EXPIRED

        user.is_verified = True
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        db.commit()
        return EmailVerificationStatus.SUCCESS
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

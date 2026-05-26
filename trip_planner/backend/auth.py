import hashlib
import os
import secrets
from enum import Enum

from flask_login import LoginManager, UserMixin


class AuthStatus(Enum):
    INVALID = "invalid"
    UNVERIFIED = "unverified"
    OK = "ok"


class User(UserMixin):
    def __init__(self, username):
        self.id = username


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def create_user(username: str, email: str, password: str, first_name: str, last_name: str) -> bool:
    """Register a new user in the DB. Returns True on success, False if username/email taken."""
    from backend.database import SessionLocal
    from backend.models import User as UserModel
    db = SessionLocal()
    try:
        email = email.strip().lower()
        if db.query(UserModel).filter(UserModel.username == username).first():
            return False
        if db.query(UserModel).filter(UserModel.email == email).first():
            return False
        salt = secrets.token_hex(16)
        hashed = _hash_password(password, salt)
        user = UserModel(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            salt=salt,
            password=hashed,
        )
        db.add(user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_user(username: str, password: str) -> bool:
    """Check credentials against the DB. Returns True if valid."""
    return authenticate_user(username, password) in {AuthStatus.OK, AuthStatus.UNVERIFIED}


def authenticate_user(username: str, password: str) -> AuthStatus:
    """Check credentials and email verification status."""
    from backend.crud import get_user_auth_record

    user = get_user_auth_record(username)
    if not user:
        return AuthStatus.INVALID

    hashed = _hash_password(password, user["salt"])
    if not secrets.compare_digest(hashed, user["password"]):
        return AuthStatus.INVALID

    if not user["is_verified"]:
        return AuthStatus.UNVERIFIED

    return AuthStatus.OK


def init_login_manager(server):
    """Attach Flask-Login to the Flask server underlying Dash."""
    server.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    login_manager = LoginManager()
    login_manager.login_view = "/login"
    login_manager.init_app(server)

    @login_manager.user_loader
    def load_user(username):
        from backend.database import SessionLocal
        from backend.models import User as UserModel
        db = SessionLocal()
        try:
            if db.query(UserModel).filter(UserModel.username == username).first():
                return User(username)
            return None
        finally:
            db.close()

    return login_manager

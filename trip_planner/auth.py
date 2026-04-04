import hashlib
import os
import secrets

from flask_login import LoginManager, UserMixin


class User(UserMixin):
    def __init__(self, username):
        self.id = username


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def create_user(username: str, password: str, first_name: str, last_name: str) -> bool:
    """Register a new user in the DB. Returns True on success, False if username taken."""
    from backend.database import SessionLocal
    from backend.models import User as UserModel
    db = SessionLocal()
    try:
        if db.query(UserModel).filter(UserModel.username == username).first():
            return False
        salt = secrets.token_hex(16)
        hashed = _hash_password(password, salt)
        user = UserModel(username=username, first_name=first_name, last_name=last_name,
                         salt=salt, password=hashed)
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
    from backend.database import SessionLocal
    from backend.models import User as UserModel
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            return False
        hashed = _hash_password(password, user.salt)
        return secrets.compare_digest(hashed, user.password)
    finally:
        db.close()


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

import os
import hashlib
import secrets
from pathlib import Path

from flask_login import LoginManager, UserMixin

# Simple JSON-file based user store
import json

USERS_FILE = Path(__file__).parent / "users.json"


class User(UserMixin):
    def __init__(self, username):
        self.id = username


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _load_users():
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def create_user(username, password):
    """Register a new user. Returns True on success, False if user exists."""
    users = _load_users()
    if username in users:
        return False
    salt = secrets.token_hex(16)
    hashed = _hash_password(password, salt)
    users[username] = {"salt": salt, "password": hashed}
    _save_users(users)
    return True


def verify_user(username, password):
    """Check credentials. Returns True if valid."""
    users = _load_users()
    if username not in users:
        return False
    record = users[username]
    hashed = _hash_password(password, record["salt"])
    return secrets.compare_digest(hashed, record["password"])


def init_login_manager(server):
    """Attach Flask-Login to the Flask server underlying Dash."""
    server.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    login_manager = LoginManager()
    login_manager.login_view = "/login"
    login_manager.init_app(server)

    @login_manager.user_loader
    def load_user(username):
        users = _load_users()
        if username in users:
            return User(username)
        return None

    return login_manager

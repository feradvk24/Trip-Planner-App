import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
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
        raw_verification_token, verification_token_hash, verification_token_expires_at = generate_verification_token()
        user = UserModel(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            salt=salt,
            password=hashed,
            verification_token_hash=verification_token_hash,
            verification_token_expires_at=verification_token_expires_at,
        )
        db.add(user)
        db.commit()
        send_verification_email(email, raw_verification_token)
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


def generate_verification_token():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    return raw_token, token_hash, expires_at


def send_verification_email(email: str, raw_token: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM_EMAIL") or smtp_username
    app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8050").rstrip("/")
    use_ssl = os.environ.get("SMTP_USE_SSL", "true").lower() in {"1", "true", "yes"}
    use_tls = os.environ.get("SMTP_USE_TLS", "false").lower() in {"1", "true", "yes"}

    if not smtp_host or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM_EMAIL or SMTP_USERNAME are required to send verification emails.")

    verification_url = f"{app_base_url}/verify-email/{raw_token}"
    message = EmailMessage()
    message["Subject"] = "Verify your Explore Bulgaria email"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        "Welcome to Explore Bulgaria.\n\n"
        "Use this link to verify your email address:\n"
        f"{verification_url}\n\n"
        "This verification link expires in 24 hours.\n\n"
    )

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if smtp_username and smtp_password:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)

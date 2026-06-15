import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from enum import Enum

from flask_login import LoginManager, UserMixin


ADMIN_PANEL_ROLES = {"admin", "moderator"}


class AuthStatus(Enum):
    INVALID = "invalid"
    INACTIVE = "inactive"
    UNVERIFIED = "unverified"
    OK = "ok"


class PasswordResetStatus(Enum):
    INVALID = "invalid"
    EXPIRED = "expired"
    SUCCESS = "success"


class User(UserMixin):
    def __init__(self, username, role="regular", is_active=True):
        self.id = username
        self.role = role
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active


def is_admin_panel_role(role) -> bool:
    return role in ADMIN_PANEL_ROLES


def is_admin_panel_user(user) -> bool:
    return bool(getattr(user, "is_authenticated", False)) and is_admin_panel_role(
        getattr(user, "role", "regular")
    )


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _is_expired(value: datetime | None) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < datetime.now(timezone.utc)


def create_user(username: str, email: str, password: str, first_name: str, last_name: str) -> bool:
    """Register a new user in the DB. Returns True on success, False if username/email taken."""
    from trip_planner.backend.db.database import SessionLocal
    from trip_planner.backend.db.models import User as UserModel
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
    from trip_planner.backend.db.crud import get_user_auth_record

    user = get_user_auth_record(username)
    if not user:
        return AuthStatus.INVALID

    hashed = _hash_password(password, user["salt"])
    if not secrets.compare_digest(hashed, user["password"]):
        return AuthStatus.INVALID

    if not user["is_active"]:
        return AuthStatus.INACTIVE

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
        from trip_planner.backend.db.database import SessionLocal
        from trip_planner.backend.db.models import User as UserModel
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.username == username).first()
            if user and user.is_active:
                return User(user.username, user.role, user.is_active)
            return None
        finally:
            db.close()

    return login_manager


def generate_verification_token():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    return raw_token, token_hash, expires_at


def generate_password_reset_token():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    return raw_token, token_hash, expires_at


def request_password_reset(email: str) -> bool:
    """Create and email a password reset token. Returns False when no eligible user exists."""
    from trip_planner.backend.db.database import SessionLocal
    from trip_planner.backend.db.models import User as UserModel

    db = SessionLocal()
    try:
        email = email.strip().lower()
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user or not user.is_active or not user.is_verified:
            return False

        raw_token, token_hash, expires_at = generate_password_reset_token()
        user.password_reset_token_hash = token_hash
        user.password_reset_expires_at = expires_at
        db.commit()
        send_password_reset_email(user.email, raw_token)
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def is_valid_password_reset_token(raw_token: str | None) -> bool:
    if not raw_token:
        return False

    from trip_planner.backend.db.database import SessionLocal
    from trip_planner.backend.db.models import User as UserModel

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.password_reset_token_hash == token_hash).first()
        if not user or not user.is_active or not user.is_verified:
            return False
        return not _is_expired(user.password_reset_expires_at)
    finally:
        db.close()


def reset_password_with_token(raw_token: str | None, new_password: str) -> PasswordResetStatus:
    if not raw_token:
        return PasswordResetStatus.INVALID

    from trip_planner.backend.db.database import SessionLocal
    from trip_planner.backend.db.models import User as UserModel

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.password_reset_token_hash == token_hash).first()
        if not user or not user.is_active or not user.is_verified:
            return PasswordResetStatus.INVALID

        if _is_expired(user.password_reset_expires_at):
            user.password_reset_token_hash = None
            user.password_reset_expires_at = None
            db.commit()
            return PasswordResetStatus.EXPIRED

        salt = secrets.token_hex(16)
        user.salt = salt
        user.password = _hash_password(new_password, salt)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.commit()
        return PasswordResetStatus.SUCCESS
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def send_verification_email(email: str, raw_token: str) -> None:
    app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8050").rstrip("/")
    verification_url = f"{app_base_url}/verify-email/{raw_token}"
    _send_auth_email(
        email,
        "Verify your Explore Bulgaria email",
        "Welcome to Explore Bulgaria.\n\n"
        "Use this link to verify your email address:\n"
        f"{verification_url}\n\n"
        "This verification link expires in 24 hours.\n\n",
    )


def send_password_reset_email(email: str, raw_token: str) -> None:
    app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8050").rstrip("/")
    password_reset_url = f"{app_base_url}/login?password_reset_token={raw_token}"
    _send_auth_email(
        email,
        "Reset your Explore Bulgaria password",
        "We received a request to reset your Explore Bulgaria password.\n\n"
        "Use this link to choose a new password:\n"
        f"{password_reset_url}\n\n"
        "This password reset link expires in 30 minutes. If you did not request it, you can ignore this email.\n\n",
    )


def _send_auth_email(email: str, subject: str, body: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM_EMAIL") or smtp_username
    use_ssl = os.environ.get("SMTP_USE_SSL", "true").lower() in {"1", "true", "yes"}
    use_tls = os.environ.get("SMTP_USE_TLS", "false").lower() in {"1", "true", "yes"}

    if not smtp_host or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM_EMAIL or SMTP_USERNAME are required to send auth emails.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = email
    message.set_content(body)

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if smtp_username and smtp_password:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)

from backend.database import SessionLocal
from backend.models import Landmark, Review, User


def _format_review(review: Review, user: User, landmark: Landmark) -> dict:
    return {
        "id": review.id,
        "username": user.username,
        "user_name": f"{user.first_name} {user.last_name}",
        "landmark_id": landmark.id,
        "landmark_name": landmark.name,
        "rating": review.rating,
        "review_text": review.review_text or "",
        "created_at": review.created_at.strftime("%d %b %Y, %H:%M"),
    }


def get_recent_reviews(limit: int = 100) -> list[dict]:
    """Return the most recent landmark reviews for the admin panel."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Review, User, Landmark)
            .join(User, Review.user_id == User.id)
            .join(Landmark, Review.landmark_id == Landmark.id)
            .order_by(Review.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_format_review(review, user, landmark) for review, user, landmark in rows]
    finally:
        db.close()


def get_reviews_by_username(username: str, limit: int = 100) -> list[dict]:
    """Return landmark reviews for a username, newest first."""
    username = (username or "").strip()
    if not username:
        return []

    db = SessionLocal()
    try:
        rows = (
            db.query(Review, User, Landmark)
            .join(User, Review.user_id == User.id)
            .join(Landmark, Review.landmark_id == Landmark.id)
            .filter(User.username.ilike(username))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_format_review(review, user, landmark) for review, user, landmark in rows]
    finally:
        db.close()


def delete_review(review_id: int) -> bool:
    """Delete a review by id. Returns True when a review was deleted."""
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if review is None:
            return False

        db.delete(review)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_role(username: str) -> dict | None:
    """Return basic user role details by username."""
    username = (username or "").strip()
    if not username:
        return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username.ilike(username)).first()
        if user is None:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "user_name": f"{user.first_name} {user.last_name}",
            "role": user.role,
        }
    finally:
        db.close()


def set_user_role(username: str, role: str) -> dict | None:
    """Set a user's role and return the updated role details."""
    username = (username or "").strip()
    if not username or role not in {"regular", "moderator"}:
        return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username.ilike(username)).first()
        if user is None:
            return None
        user.role = role
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "user_name": f"{user.first_name} {user.last_name}",
            "role": user.role,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

from trip_planner.backend.db.database import SessionLocal
from trip_planner.backend.db.models import Landmark, Review, User


def _build_access_point(access_latitude, access_longitude) -> dict | None:
    if access_latitude is None or access_longitude is None:
        return None
    return {"lat": float(access_latitude), "lon": float(access_longitude)}


def _refresh_landmark_registry():
    from trip_planner.services.landmark_registry import LandmarkRegistry

    LandmarkRegistry._instance = None


def _format_landmark(landmark: Landmark) -> dict:
    access_point = landmark.access_point or {}
    return {
        "id": landmark.id,
        "name": landmark.name,
        "location": landmark.location or "",
        "latitude": landmark.latitude,
        "longitude": landmark.longitude,
        "link": landmark.link or "",
        "access_latitude": access_point.get("lat"),
        "access_longitude": access_point.get("lon"),
    }


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


def get_landmark(landmark_id: int) -> dict | None:
    """Return editable landmark details by id."""
    db = SessionLocal()
    try:
        landmark = db.query(Landmark).filter(Landmark.id == landmark_id).first()
        return _format_landmark(landmark) if landmark else None
    finally:
        db.close()


def create_landmark(
    name: str,
    location: str,
    latitude,
    longitude,
    link: str = "",
    access_latitude=None,
    access_longitude=None,
) -> dict:
    """Create a landmark and return its editable details."""
    db = SessionLocal()
    try:
        landmark = Landmark(
            name=name.strip(),
            location=(location or "").strip() or None,
            latitude=float(latitude),
            longitude=float(longitude),
            link=(link or "").strip() or None,
            access_point=_build_access_point(access_latitude, access_longitude),
        )
        db.add(landmark)
        db.commit()
        db.refresh(landmark)
        _refresh_landmark_registry()
        return _format_landmark(landmark)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_landmark(
    landmark_id: int,
    name: str,
    location: str,
    latitude,
    longitude,
    link: str = "",
    access_latitude=None,
    access_longitude=None,
) -> dict | None:
    """Update a landmark and return its editable details."""
    db = SessionLocal()
    try:
        landmark = db.query(Landmark).filter(Landmark.id == landmark_id).first()
        if landmark is None:
            return None

        landmark.name = name.strip()
        landmark.location = (location or "").strip() or None
        landmark.latitude = float(latitude)
        landmark.longitude = float(longitude)
        landmark.link = (link or "").strip() or None
        landmark.access_point = _build_access_point(access_latitude, access_longitude)
        db.commit()
        db.refresh(landmark)
        _refresh_landmark_registry()
        return _format_landmark(landmark)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
            "is_active": user.is_active,
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
            "is_active": user.is_active,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_user_active_status(username: str, is_active: bool) -> dict | None:
    """Set a user's active status and return the updated role details."""
    username = (username or "").strip()
    if not username:
        return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username.ilike(username)).first()
        if user is None:
            return None
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "user_name": f"{user.first_name} {user.last_name}",
            "role": user.role,
            "is_active": user.is_active,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

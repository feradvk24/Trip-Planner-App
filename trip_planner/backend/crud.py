from backend.database import SessionLocal
from backend.models import User, UserTrip


def save_trip(username: str, name: str, landmark_ids: list, visit_order: list,
              used_user_location_start: bool = False, used_user_location_end: bool = False) -> UserTrip:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = UserTrip(
            user_id=user.id,
            name=name,
            landmark_ids=landmark_ids,
            visit_order=visit_order,
            used_user_location_start=used_user_location_start,
            used_user_location_end=used_user_location_end,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_trips(username: str) -> list[dict]:
    """Return all trips for a user, newest first."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return []
        trips = (
            db.query(UserTrip)
            .filter(UserTrip.user_id == user.id)
            .order_by(UserTrip.created_at.desc())
            .all()
        )
        return [
            {
                "id": t.id,
                "name": t.name,
                "landmark_ids": t.landmark_ids,
                "visit_order": t.visit_order,
                "used_user_location_start": t.used_user_location_start,
                "used_user_location_end": t.used_user_location_end,
                "created_at": t.created_at.strftime("%d %b %Y, %H:%M"),
            }
            for t in trips
        ]
    finally:
        db.close()

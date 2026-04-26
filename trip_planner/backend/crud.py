from backend.database import SessionLocal
from backend.models import User, UserTrip


def save_trip(username: str, name: str, landmark_ids: list, visit_order: list,
              route_legs: list = None, custom_start_location: dict = None,
              custom_end_location: dict = None, saved_user_location: dict = None) -> UserTrip:
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
            route_legs=route_legs or [],
            custom_start_location=custom_start_location,
            custom_end_location=custom_end_location,
            saved_user_location=saved_user_location,
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
                "route_legs": t.route_legs or [],
                "custom_start_location": t.custom_start_location,
                "custom_end_location": t.custom_end_location,
                "saved_user_location": t.saved_user_location,
                "current_point_index": t.current_point_index,
                "visited_indices": t.visited_indices or [],
                "created_at": t.created_at.strftime("%d %b %Y, %H:%M"),
            }
            for t in trips
        ]
    finally:
        db.close()


def update_trip_progress(trip_id: int, new_current_index: int, newly_visited_index: int) -> None:
    """Advance a trip's current point and record the just-visited index."""
    db = SessionLocal()
    try:
        trip = db.query(UserTrip).filter(UserTrip.id == trip_id).first()
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        visited = list(trip.visited_indices or [])
        if newly_visited_index not in visited:
            visited.append(newly_visited_index)
        trip.visited_indices = visited
        trip.current_point_index = new_current_index
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_trip(username: str, trip_id: int) -> None:
    """Delete one of a user's trips by ID."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = (
            db.query(UserTrip)
            .filter(UserTrip.id == trip_id, UserTrip.user_id == user.id)
            .first()
        )
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        db.delete(trip)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

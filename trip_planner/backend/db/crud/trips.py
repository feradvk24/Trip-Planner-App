from typing import Optional

from trip_planner.backend.db.database import SessionLocal
from trip_planner.backend.db.models import TripCompletion, User, UserLandmarkVisit, UserTrip


def _normalize_trip_name(name: str) -> str:
    return (name or "").strip().casefold()


def _visible_user_trips(db):
    return db.query(UserTrip).filter(UserTrip.is_deleted.is_(False))


def _visible_public_trips(db):
    return (
        db.query(UserTrip, User)
        .join(User, UserTrip.user_id == User.id)
        .filter(UserTrip.is_deleted.is_(False), UserTrip.is_public.is_(True))
    )


def _trip_to_dict(trip: UserTrip, owner: Optional[User] = None) -> dict:
    data = {
        "id": trip.id,
        "name": trip.name,
        "landmark_ids": trip.landmark_ids,
        "visit_order": trip.visit_order,
        "route_legs": trip.route_legs or [],
        "custom_start_location": trip.custom_start_location,
        "custom_end_location": trip.custom_end_location,
        "saved_user_location": trip.saved_user_location,
        "current_point_index": trip.current_point_index,
        "visited_indices": trip.visited_indices or [],
        "is_public": trip.is_public,
        "is_deleted": trip.is_deleted,
        "created_at": trip.created_at.strftime("%d %b %Y, %H:%M"),
    }
    if owner:
        data["owner_username"] = owner.username
        data["owner_name"] = f"{owner.first_name} {owner.last_name}"
    return data


def _completion_to_status(completion: TripCompletion) -> dict:
    return {
        "completed_at": completion.completed_at.strftime("%d %b %Y, %H:%M"),
        "completion_rating": completion.rating,
        "completion_review_text": completion.review_text,
    }


def find_completed_trips(trip_ids: list[int]) -> dict[int, dict]:
    """Return completion statuses keyed by trip ID."""
    if not trip_ids:
        return {}
    db = SessionLocal()
    try:
        completed_trips = {}
        for trip_id in trip_ids:
            completion = (
                db.query(TripCompletion)
                .filter(TripCompletion.trip_id == trip_id)
                .limit(1)
                .first()
            )
            if completion:
                completed_trips[trip_id] = _completion_to_status(completion)
        return completed_trips
    finally:
        db.close()


def _with_completion_statuses(trips: list[dict]) -> list[dict]:
    completed_trips = find_completed_trips([trip["id"] for trip in trips])
    return [
        {
            **trip,
            "completed_at": completed_trips.get(trip["id"], {}).get("completed_at"),
            "completion_rating": completed_trips.get(trip["id"], {}).get("completion_rating"),
            "completion_review_text": completed_trips.get(trip["id"], {}).get("completion_review_text"),
        }
        for trip in trips
    ]


def user_trip_name_exists(username: str, name: str) -> bool:
    """Return whether a user already has a trip with the same normalized name."""
    normalized_name = _normalize_trip_name(name)
    if not normalized_name:
        return False
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return False
        trips = _visible_user_trips(db).with_entities(UserTrip.name).filter(UserTrip.user_id == user.id).all()
        return any(_normalize_trip_name(trip_name) == normalized_name for (trip_name,) in trips)
    finally:
        db.close()


def save_trip(username: str, name: str, landmark_ids: list, visit_order: list,
              route_legs: list = None, custom_start_location: dict = None,
              custom_end_location: dict = None, saved_user_location: dict = None) -> UserTrip:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        normalized_name = _normalize_trip_name(name)
        existing_names = _visible_user_trips(db).with_entities(UserTrip.name).filter(UserTrip.user_id == user.id).all()
        if any(_normalize_trip_name(trip_name) == normalized_name for (trip_name,) in existing_names):
            raise ValueError("You already have a saved trip with this name.")
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


def get_user_trips(username: str, include_completion_status: bool = False) -> list[dict]:
    """Return all trips for a user, newest first."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return []
        trips = (
            _visible_user_trips(db)
            .filter(UserTrip.user_id == user.id)
            .order_by(UserTrip.created_at.desc())
            .all()
        )
        trip_data = [_trip_to_dict(t) for t in trips]
        if include_completion_status:
            return _with_completion_statuses(trip_data)
        return trip_data
    finally:
        db.close()


def get_active_user_trip(username: str) -> dict | None:
    """Return the user's active trip in the shape used by ACTIVE_TRIP_STORE."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None or user.active_trip_id is None:
            return None
        trip = (
            _visible_user_trips(db)
            .filter(
                UserTrip.id == user.active_trip_id,
                UserTrip.user_id == user.id,
            )
            .first()
        )
        if trip is None:
            user.active_trip_id = None
            db.commit()
            return None
        return {**_trip_to_dict(trip), "trip_id": trip.id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_active_user_trip(username: str, trip_id: int) -> dict:
    """Set one of the user's saved trips as the trip to load by default."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = (
            _visible_user_trips(db)
            .filter(
                UserTrip.id == trip_id,
                UserTrip.user_id == user.id,
            )
            .first()
        )
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        user.active_trip_id = trip.id
        db.commit()
        db.refresh(trip)
        return {**_trip_to_dict(trip), "trip_id": trip.id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def clear_active_user_trip(username: str) -> None:
    """Clear the user's active trip."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        user.active_trip_id = None
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_public_trips(include_completion_status: bool = False) -> list[dict]:
    """Return public trips from all users, newest first."""
    db = SessionLocal()
    try:
        trips = _visible_public_trips(db).order_by(UserTrip.created_at.desc()).all()
        trip_data = [_trip_to_dict(trip, owner) for trip, owner in trips]
        if include_completion_status:
            return _with_completion_statuses(trip_data)
        return trip_data
    finally:
        db.close()


def get_public_trip(trip_id: int) -> dict | None:
    """Return one public trip by id."""
    db = SessionLocal()
    try:
        row = (
            _visible_public_trips(db)
            .filter(
                UserTrip.id == trip_id,
            )
            .first()
        )
        if not row:
            return None
        trip, owner = row
        return _trip_to_dict(trip, owner)
    finally:
        db.close()


def set_trip_public_status(username: str, trip_id: int, is_public: bool) -> None:
    """Set whether one of a user's trips is visible in the public shared browser."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = (
            _visible_user_trips(db)
            .filter(
                UserTrip.id == trip_id,
                UserTrip.user_id == user.id,
            )
            .first()
        )
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        trip.is_public = is_public
        db.commit()
    except Exception:
        db.rollback()
        raise
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

        visit_order = trip.visit_order or []
        if 0 <= newly_visited_index < len(visit_order):
            landmark_id = visit_order[newly_visited_index]
            if landmark_id != -1:
                existing_visit = (
                    db.query(UserLandmarkVisit)
                    .filter(
                        UserLandmarkVisit.user_id == trip.user_id,
                        UserLandmarkVisit.landmark_id == landmark_id,
                        UserLandmarkVisit.trip_id == trip.id,
                    )
                    .first()
                )
                if existing_visit is None:
                    db.add(UserLandmarkVisit(
                        user_id=trip.user_id,
                        landmark_id=landmark_id,
                        trip_id=trip.id,
                    ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_trip(username: str, trip_id: int) -> None:
    """Hide one of a user's trips without removing its history rows."""
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
        if user.active_trip_id == trip.id:
            user.active_trip_id = None
        trip.is_deleted = True
        trip.is_public = False
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

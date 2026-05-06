from typing import Optional

from backend.database import SessionLocal
from backend.models import Landmark, Review, TripCompletion, User, UserTrip


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
        "created_at": trip.created_at.strftime("%d %b %Y, %H:%M"),
    }
    if owner:
        data["owner_username"] = owner.username
        data["owner_name"] = f"{owner.first_name} {owner.last_name}"
    return data


def _completion_to_status(completion: TripCompletion) -> dict:
    return {
        "is_completed": True,
        "completed_at": completion.completed_at.strftime("%d %b %Y, %H:%M"),
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


def get_landmark_review_summary(landmark_id: int) -> dict:
    """Return average rating and review count for a landmark."""
    db = SessionLocal()
    try:
        reviews = db.query(Review).filter(Review.landmark_id == landmark_id).all()
        review_count = len(reviews)
        average_rating = (
            sum(review.rating for review in reviews) / review_count
            if review_count else
            None
        )
        return {
            "average_rating": average_rating,
            "review_count": review_count,
        }
    finally:
        db.close()


def get_landmark_reviews(landmark_id: int) -> list[dict]:
    """Return reviews for a landmark, newest first."""
    db = SessionLocal()
    try:
        reviews = (
            db.query(Review, User)
            .join(User, Review.user_id == User.id)
            .filter(Review.landmark_id == landmark_id)
            .order_by(Review.created_at.desc())
            .all()
        )
        return [
            {
                "id": review.id,
                "rating": review.rating,
                "review_text": review.review_text,
                "created_at": review.created_at.strftime("%d %b %Y, %H:%M"),
                "user_name": f"{user.first_name} {user.last_name}",
                "username": user.username,
            }
            for review, user in reviews
        ]
    finally:
        db.close()


def _with_completion_statuses(trips: list[dict]) -> list[dict]:
    completed_trips = find_completed_trips([trip["id"] for trip in trips])
    return [
        {
            **trip,
            "is_completed": trip["id"] in completed_trips,
            "completed_at": completed_trips.get(trip["id"], {}).get("completed_at"),
        }
        for trip in trips
    ]


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


def get_user_trips(username: str, include_completion_status: bool = False) -> list[dict]:
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
        trip_data = [_trip_to_dict(t) for t in trips]
        if include_completion_status:
            return _with_completion_statuses(trip_data)
        return trip_data
    finally:
        db.close()


def get_public_trips(include_completion_status: bool = False) -> list[dict]:
    """Return public trips from all users, newest first."""
    db = SessionLocal()
    try:
        trips = (
            db.query(UserTrip, User)
            .join(User, UserTrip.user_id == User.id)
            .filter(UserTrip.is_public.is_(True))
            .order_by(UserTrip.created_at.desc())
            .all()
        )
        trip_data = [_trip_to_dict(trip, owner) for trip, owner in trips]
        if include_completion_status:
            return _with_completion_statuses(trip_data)
        return trip_data
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
            db.query(UserTrip)
            .filter(UserTrip.id == trip_id, UserTrip.user_id == user.id)
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
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_landmark_review(username: str, trip_id: int, landmark_id: int, rating: int, review_text: str = None) -> Review:
    """Create a review for a landmark visited during a trip."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = db.query(UserTrip).filter(UserTrip.id == trip_id).first()
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        landmark = db.query(Landmark).filter(Landmark.id == landmark_id).first()
        if landmark is None:
            raise ValueError(f"Landmark {landmark_id} not found.")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        review = Review(
            user_id=user.id,
            trip_id=trip.id,
            landmark_id=landmark.id,
            rating=rating,
            review_text=(review_text or "").strip() or None,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_trip_completion(username: str, trip_id: int, rating: int, review_text: str = None) -> TripCompletion:
    """Create a completion record for a finished trip."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = db.query(UserTrip).filter(UserTrip.id == trip_id).first()
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        completion = TripCompletion(
            user_id=user.id,
            trip_id=trip.id,
            rating=rating,
            review_text=(review_text or "").strip() or None,
        )
        db.add(completion)
        db.commit()
        db.refresh(completion)
        return completion
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

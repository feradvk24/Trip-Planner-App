from typing import Optional
from collections import Counter
from datetime import datetime, timezone

from backend.database import SessionLocal
from backend.models import Landmark as LandmarkModel, LandmarkImage, Review, TripCompletion, User, UserTrip, UserLandmarkVisit


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


def _month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: datetime, months: int) -> datetime:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return value.replace(year=year, month=month)


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


def get_user_email(username: str) -> str | None:
    """Return the email address for a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.email if user else None
    finally:
        db.close()


def get_user_auth_record(username: str) -> dict | None:
    """Return the fields needed to authenticate a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return {
            "username": user.username,
            "salt": user.salt,
            "password": user.password,
            "is_verified": user.is_verified,
        }
    finally:
        db.close()


def get_landmarks() -> list[dict]:
    """Return all landmarks in the shape used by LandmarkRegistry."""
    db = SessionLocal()
    try:
        rows = db.query(LandmarkModel).all()
        return [
            {
                "id": row.id,
                "name": row.name,
                "location": row.location or "Location",
                "lat": row.latitude,
                "lon": row.longitude,
                "link": row.link or "#",
                "access_point": row.access_point,
            }
            for row in rows
        ]
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


def _landmark_image_to_dict(image: LandmarkImage) -> dict:
    return {
        "id": image.id,
        "landmark_id": image.landmark_id,
        "commons_file": image.commons_file,
        "image_url": image.image_url,
        "src_link": image.image_url,
        "image_source_url": image.image_source_url,
        "author": image.author,
        "license": image.license,
        "license_url": image.license_url,
        "fetched_at": image.fetched_at.isoformat() if image.fetched_at else None,
    }


def get_landmark_image(landmark_id: int) -> dict | None:
    """Return the image metadata for a landmark, if one exists."""
    db = SessionLocal()
    try:
        image = (
            db.query(LandmarkImage)
            .filter(LandmarkImage.landmark_id == landmark_id)
            .first()
        )
        return _landmark_image_to_dict(image) if image else None
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
        landmark = db.query(LandmarkModel).filter(LandmarkModel.id == landmark_id).first()
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


def create_trip_completion(username: str, trip_id: int, rating: int | None = None, review_text: str = None) -> TripCompletion:
    """Create or update a completion record for a finished trip."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise ValueError(f"User '{username}' not found in database.")
        trip = db.query(UserTrip).filter(UserTrip.id == trip_id).first()
        if trip is None:
            raise ValueError(f"Trip {trip_id} not found.")
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5.")

        completion = (
            db.query(TripCompletion)
            .filter(
                TripCompletion.user_id == user.id,
                TripCompletion.trip_id == trip.id,
            )
            .order_by(TripCompletion.completed_at.desc())
            .first()
        )
        if completion is None:
            completion = TripCompletion(
                user_id=user.id,
                trip_id=trip.id,
                rating=rating,
                review_text=(review_text or "").strip() or None,
            )
            db.add(completion)
        else:
            if rating is not None:
                completion.rating = rating
            if review_text is not None:
                completion.review_text = review_text.strip() or None
        db.commit()
        db.refresh(completion)
        return completion
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


def get_user_visited_landmark_ids(username: str) -> set[int]:
    """Return distinct landmark IDs visited by the user across all trips."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return set()

        rows = (
            db.query(UserLandmarkVisit.landmark_id)
            .filter(UserLandmarkVisit.user_id == user.id)
            .distinct()
            .all()
        )
        return {landmark_id for (landmark_id,) in rows}
    finally:
        db.close()

def get_user_landmark_visit_history(username: str, landmark_id: int | None = None, limit: int | None = None) -> list[dict]:
    """Return a user's landmark visit history, newest first."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return []

        query = (
            db.query(UserLandmarkVisit, UserTrip)
            .join(UserTrip, UserLandmarkVisit.trip_id == UserTrip.id)
            .filter(UserLandmarkVisit.user_id == user.id)
        )
        if landmark_id is not None:
            query = query.filter(UserLandmarkVisit.landmark_id == landmark_id)

        query = query.order_by(UserLandmarkVisit.visited_at.desc())
        if limit is not None:
            query = query.limit(limit)

        visits = query.all()
        return [
            {
                "id": visit.id,
                "landmark_id": visit.landmark_id,
                "trip_id": visit.trip_id,
                "trip_name": trip.name,
                "visited_at": visit.visited_at.strftime("%d %b %Y, %H:%M"),
            }
            for visit, trip in visits
        ]
    finally:
        db.close()


def get_user_monthly_landmark_visit_counts(username: str, months: int = 6) -> list[dict]:
    """Return landmark visit counts for the most recent calendar months."""
    if months < 1:
        return []

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return []

        current_month = _month_start(datetime.now(timezone.utc))
        first_month = _add_months(current_month, -(months - 1))
        rows = (
            db.query(UserLandmarkVisit.visited_at)
            .filter(
                UserLandmarkVisit.user_id == user.id,
                UserLandmarkVisit.visited_at >= first_month,
            )
            .all()
        )
        counts = Counter((visited_at.year, visited_at.month) for (visited_at,) in rows)

        return [
            {
                "month": bucket.strftime("%b %Y"),
                "year": bucket.year,
                "month_number": bucket.month,
                "count": counts.get((bucket.year, bucket.month), 0),
            }
            for bucket in (_add_months(first_month, offset) for offset in range(months))
        ]
    finally:
        db.close()


def total_landmark_visits_for_user(username: str) -> int:
    """Return the total number of landmark visits across all of the user's trips."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            return 0

        count = (
            db.query(UserLandmarkVisit)
            .filter(UserLandmarkVisit.user_id == user.id)
            .count()
        )
        return count
    finally:
        db.close()

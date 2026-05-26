from backend.database import SessionLocal
from backend.models import Landmark as LandmarkModel, Review, TripCompletion, User, UserTrip


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

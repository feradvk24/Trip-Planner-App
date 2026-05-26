from backend.database import SessionLocal
from backend.models import Landmark as LandmarkModel, LandmarkImage, Review


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

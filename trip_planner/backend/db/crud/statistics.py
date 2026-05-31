from collections import Counter
from datetime import datetime, timezone

from backend.db.database import SessionLocal
from backend.db.models import User, UserLandmarkVisit, UserTrip


def _month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: datetime, months: int) -> datetime:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return value.replace(year=year, month=month)


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

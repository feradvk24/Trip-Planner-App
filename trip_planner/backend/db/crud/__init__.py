from backend.db.crud.landmarks import (
    get_landmark_image,
    get_landmark_review_summary,
    get_landmarks,
)
from backend.db.crud.reviews import (
    create_landmark_review,
    create_trip_completion,
    get_landmark_reviews,
)
from backend.db.crud.statistics import (
    get_user_landmark_visit_history,
    get_user_monthly_landmark_visit_counts,
    get_user_visited_landmark_ids,
    total_landmark_visits_for_user,
)
from backend.db.crud.trips import (
    clear_active_user_trip,
    delete_trip,
    find_completed_trips,
    get_active_user_trip,
    get_public_trip,
    get_public_trips,
    get_user_trips,
    save_trip,
    set_active_user_trip,
    set_trip_public_status,
    update_trip_progress,
    user_trip_name_exists,
)
from backend.db.crud.users import (
    EmailVerificationStatus,
    get_user_auth_record,
    get_user_email,
    verify_user_email_token,
)

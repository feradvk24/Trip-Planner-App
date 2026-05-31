from dataclasses import dataclass

from backend.crud import (
    clear_active_user_trip,
    create_landmark_review,
    create_trip_completion,
    save_trip,
    set_active_user_trip,
    set_trip_public_status,
    update_trip_progress,
    user_trip_name_exists,
)
from schemas.stores import (
    ActiveTripStore,
    OptimizedTripStore,
    ReviewStateStore,
    SelectedTripStore,
    ServiceResultData,
)
from services.trip_route import TripRoute


@dataclass(frozen=True)
class ServiceResult:
    ok: bool
    code: str = "ok"
    data: ServiceResultData | None = None
    error: str | None = None


def save_optimized_trip_for_user(
    username: str,
    name: str | None,
    landmark_ids: list[int] | None,
    optimized_trip: OptimizedTripStore | None,
) -> ServiceResult:
    trip_name = (name or "").strip()
    if not trip_name:
        return ServiceResult(False, "missing_name")
    if user_trip_name_exists(username, trip_name):
        return ServiceResult(False, "name_exists")
    if not optimized_trip:
        return ServiceResult(False, "missing_route")

    custom_start_location = optimized_trip.get("custom_start_location")
    custom_end_location = optimized_trip.get("custom_end_location")
    saved_user_location = custom_start_location or custom_end_location
    stop_ids = TripRoute.handle_trip_store(optimized_trip)["destination_ids"]

    try:
        save_trip(
            username=username,
            name=trip_name,
            landmark_ids=landmark_ids or [],
            visit_order=stop_ids,
            route_legs=optimized_trip.get("route_legs") or [],
            custom_start_location=custom_start_location,
            custom_end_location=custom_end_location,
            saved_user_location=saved_user_location,
        )
    except Exception as exc:
        return ServiceResult(False, "failed", error=str(exc))

    return ServiceResult(True)


def load_selected_trip_for_user(username: str, trip: SelectedTripStore) -> ServiceResult:
    if trip.get("source") == "shared":
        clear_active_user_trip(username)
        return ServiceResult(
            True,
            data={
                "pending_browse_trip": {
                    "shared_trip_id": trip["id"],
                },
            },
        )

    set_active_user_trip(username, trip["id"])
    return ServiceResult(True)


def share_active_trip_for_user(username: str, active_trip: ActiveTripStore | None) -> ServiceResult:
    if not active_trip or not active_trip.get("trip_id"):
        return ServiceResult(False, "not_loaded")
    if active_trip.get("is_public"):
        return ServiceResult(False, "already_shared", data={"updated_trip": active_trip})

    try:
        set_trip_public_status(username, active_trip["trip_id"], True)
    except Exception as exc:
        return ServiceResult(False, "failed", error=str(exc))

    return ServiceResult(True, data={"updated_trip": {**active_trip, "is_public": True}})


def visit_trip_stop_for_user(
    username: str,
    active_trip: ActiveTripStore | None,
    clicked_index: int | None,
    route: TripRoute | None = None,
) -> ServiceResult:
    if not active_trip or clicked_index is None:
        raise ValueError("A trip and stop index are required.")

    route = route or TripRoute.from_store(active_trip)
    was_already_complete = route.is_complete
    route.visit(clicked_index)

    update_trip_progress(
        trip_id=active_trip["trip_id"],
        new_current_index=clicked_index,
        newly_visited_index=clicked_index,
    )
    updated_trip = {
        **active_trip,
        "current_point_index": clicked_index,
        "visited_indices": sorted(route.visited_indices),
    }

    if route.is_complete and not was_already_complete:
        create_trip_completion(
            username=username,
            trip_id=updated_trip["trip_id"],
        )

    return ServiceResult(
        True,
        data={
            "updated_trip": updated_trip,
            "was_already_complete": was_already_complete,
            "is_now_complete": route.is_complete,
        },
    )


def submit_trip_or_landmark_review_for_user(
    username: str,
    active_trip: ActiveTripStore | None,
    review_state: ReviewStateStore | None,
    review_text: str | None,
) -> ServiceResult:
    review_state = review_state or {}
    is_trip_completion_review = review_state.get("review_type") == "trip_completion"
    landmark_id = review_state.get("landmark_id")
    rating = review_state.get("rating")

    if not active_trip or not active_trip.get("trip_id") or (not is_trip_completion_review and not landmark_id):
        return ServiceResult(False, "missing_target")
    if rating is None:
        return ServiceResult(False, "missing_rating")

    try:
        if is_trip_completion_review:
            create_trip_completion(
                username=username,
                trip_id=active_trip["trip_id"],
                rating=int(rating),
                review_text=review_text,
            )
        else:
            create_landmark_review(
                username=username,
                trip_id=active_trip["trip_id"],
                landmark_id=int(landmark_id),
                rating=int(rating),
                review_text=review_text,
            )
    except Exception as exc:
        return ServiceResult(False, "failed", error=str(exc))

    return ServiceResult(True)

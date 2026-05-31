from typing import Literal, TypedDict


class LocationStore(TypedDict):
    """JSON shape used for saved custom start/end locations in dcc.Store."""

    lat: float
    lon: float


class RouteLegStore(TypedDict, total=False):
    """Route segment shape stored in ACTIVE_TRIP_STORE and OPTIMIZED_TRIP_STORE."""

    from_index: int
    to_index: int
    polyline: str
    distance_m: float
    duration_s: float


class OptimizedTripStore(TypedDict, total=False):
    """Expected data shape for ids.OPTIMIZED_TRIP_STORE."""

    visit_order: list[int]
    route_legs: list[RouteLegStore]
    custom_start_location: LocationStore | None
    custom_end_location: LocationStore | None
    total_distance_m: float
    total_duration_s: float


class ActiveTripStore(OptimizedTripStore, total=False):
    """Expected data shape for ids.ACTIVE_TRIP_STORE."""

    id: int
    trip_id: int
    name: str
    landmark_ids: list[int]
    saved_user_location: LocationStore | None
    current_point_index: int
    visited_indices: list[int]
    is_public: bool
    is_deleted: bool
    created_at: str


class SelectedTripStore(ActiveTripStore, total=False):
    """Expected data shape for ids.SELECTED_TRIP_STORE."""

    source: Literal["saved", "shared"]
    owner_username: str
    owner_name: str
    completed_at: str | None
    completion_rating: int | None
    completion_review_text: str | None


class ActiveInfoStore(TypedDict):
    """Expected data shape for ids.ACTIVE_INFO_STORE."""

    type: Literal["trip", "landmark"]
    content: int


class ReviewStateStore(TypedDict, total=False):
    """Expected data shape for ids.LANDMARK_REVIEW_STATE_STORE."""

    is_open: bool
    review_type: Literal["landmark", "trip_completion"]
    landmark_id: int
    trip_id: int
    title: str
    location: str
    rating: int | None
    next_review_state: "ReviewStateStore"


class PendingBrowseTripStore(TypedDict, total=False):
    """Server-session payload used to hydrate dcc.Store values after browsing trips."""

    shared_trip_id: int
    active_trip: ActiveTripStore | None
    mode: Literal["explore", "trip"]
    destination_ids: list[int]
    visit_order: list[int]
    optimized_trip: OptimizedTripStore | None


class ServiceResultData(TypedDict, total=False):
    """Typed payload keys returned by service workflow functions."""

    pending_browse_trip: PendingBrowseTripStore
    updated_trip: ActiveTripStore
    was_already_complete: bool
    is_now_complete: bool

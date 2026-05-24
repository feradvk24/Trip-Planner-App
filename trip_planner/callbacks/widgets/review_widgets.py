from dash import html
from dash.exceptions import PreventUpdate

from i18n import t

def landmark_review_pane_style(display="none"):
    return {
        "display": display,
        "position": "fixed",
        "inset": 0,
        "zIndex": 11000,
        "alignItems": "center",
        "justifyContent": "center",
        "backgroundColor": "rgba(248, 249, 250, 0.42)",
        "backdropFilter": "blur(1px)",
        "pointerEvents": "auto",
    }


def landmark_review_star_buttons(rating=None, lang="bg"):
    rating = int(rating or 0)
    return [
        html.Button(
            [
                html.I(className="bi bi-star-fill"),
                html.Span(t("landmark_review.stars", lang=lang).format(count=i), className="visually-hidden"),
            ],
            id={"type": "landmark-review-star-btn", "index": i},
            type="button",
            className=(
                "landmark-review-star landmark-review-star-active"
                if i <= rating else
                "landmark-review-star"
            ),
        )
        for i in range(1, 6)
    ]


def review_pane_state(registry, active_trip, visited_index):
    stop_ids = active_trip.get("visit_order") or []
    if visited_index is None or visited_index < 0 or visited_index >= len(stop_ids):
        raise PreventUpdate
    landmark_id = stop_ids[visited_index]
    if landmark_id == -1:
        raise PreventUpdate
    landmark = registry.get_landmark(landmark_id)
    if not landmark:
        raise PreventUpdate
    return {
        "is_open": True,
        "review_type": "landmark",
        "landmark_id": landmark.id,
        "title": landmark.name,
        "location": landmark.location,
        "rating": None,
    }


def trip_completion_review_pane_state(active_trip):
    trip_name = active_trip.get("name") or active_trip.get("trip_name") or active_trip.get("title") or "Trip"
    return {
        "is_open": True,
        "review_type": "trip_completion",
        "trip_id": active_trip.get("trip_id"),
        "title": "Trip complete!",
        "location": trip_name,
        "rating": None,
    }

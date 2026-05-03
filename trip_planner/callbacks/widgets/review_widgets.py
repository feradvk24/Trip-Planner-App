from dash import html
from dash.exceptions import PreventUpdate


def landmark_review_pane_style(display="none"):
    return {
        "display": display,
        "position": "absolute",
        "inset": 0,
        "zIndex": 1001,
        "alignItems": "center",
        "justifyContent": "center",
        "backgroundColor": "rgba(248, 249, 250, 0.42)",
        "backdropFilter": "blur(1px)",
        "pointerEvents": "auto",
    }


def landmark_review_star_buttons(rating=None):
    rating = int(rating or 0)
    return [
        html.Button(
            [
                html.I(className="bi bi-star-fill"),
                html.Span(f"{i} stars", className="visually-hidden"),
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
        "landmark_id": landmark.id,
        "title": landmark.name,
        "location": landmark.location,
        "rating": None,
    }

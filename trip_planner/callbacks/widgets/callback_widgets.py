import dash_bootstrap_components as dbc
from dash import html

from layout.markers import create_markers
from styles import checkbox_icon, pin_icon


def button_label_text(children):
    if isinstance(children, str):
        return children
    if isinstance(children, list):
        return "".join(child for child in children if isinstance(child, str)).strip()
    return ""


def optimize_route_button_children(label):
    icon_class = "bi bi-pencil-square me-2" if label == "Modify Route" else "bi bi-signpost-split me-2"
    return [html.I(className=icon_class), label]


def build_all_markers(landmarks, destination_ids):
    return create_markers(landmarks, pin_icon, destination_ids, checkbox_icon)


def build_load_trip_items(trips, allow_delete=True, show_owner=False):
    if not trips:
        return [dbc.ListGroupItem("No trips to show...", disabled=True)]
    return [
        dbc.ListGroupItem(
            html.Div(
                [component for component in [
                    html.Button(
                        [component for component in [
                            html.Div(trip["name"], style={"fontWeight": "600"}),
                            html.Small(
                                f"Shared by {trip.get('owner_name') or trip.get('owner_username')}",
                                className="text-muted d-block",
                            ) if show_owner else None,
                            html.Small(trip["created_at"], className="text-muted"),
                        ] if component is not None],
                        id={"type": "load-trip-item", "index": trip["id"]},
                        n_clicks=0,
                        style={
                            "background": "none",
                            "border": "none",
                            "padding": 0,
                            "textAlign": "left",
                            "flex": "1 1 auto",
                            "minWidth": 0,
                            "cursor": "pointer",
                        },
                    ),
                    dbc.Button(
                        "X",
                        id={"type": "delete-trip-item", "index": trip["id"]},
                        n_clicks=0,
                        color="link",
                        size="sm",
                        title="Delete trip",
                        style={
                            "color": "#dc3545",
                            "fontWeight": "700",
                            "textDecoration": "none",
                            "flex": "0 0 auto",
                        },
                    ) if allow_delete else None,
                ] if component is not None],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "0.75rem",
                },
            ),
            className="saved-trip-item",
        )
        for trip in trips
    ]


def build_selected_object_items(registry, destination_ids):
    return [
        dbc.ListGroupItem([
            html.H6(landmark.name, className="mb-1 small"),
            html.P(landmark.location, className="mb-1 small"),
        ], className="p-3", id=f"selected-item-{landmark.id}")
        for landmark in registry.get_landmarks(destination_ids or [])
    ]

import dash_bootstrap_components as dbc
from dash import html

from i18n import t
from layout.markers import create_markers
from styles import checkbox_icon, pin_icon


def optimize_route_button_children(label, is_modify=False):
    icon_class = "bi bi-pencil-square me-2" if is_modify else "bi bi-signpost-split me-2"
    return [html.I(className=icon_class), label]


def build_all_markers(landmarks, destination_ids, hidden_ids=None, lang="bg"):
    hidden_ids = set(hidden_ids or [])
    visible_landmarks = [
        landmark for landmark in landmarks
        if landmark.id not in hidden_ids
    ]
    return create_markers(visible_landmarks, pin_icon, destination_ids, checkbox_icon, lang=lang)


def build_load_trip_items(trips, allow_delete=True, show_owner=False, lang="bg"):
    if not trips:
        return [dbc.ListGroupItem(t("trip_list.empty", lang=lang), disabled=True)]

    return [
        dbc.ListGroupItem(
            html.Div(
                [component for component in [
                    html.Button(
                        [component for component in [
                            html.Div(trip["name"], style={"fontWeight": "600"}),
                            html.Small(
                                f"{t('trip_list.shared_by', lang=lang)} {trip.get('owner_name') or trip.get('owner_username')}",
                                className="text-muted d-block",
                            ) if show_owner else None,
                            html.Small(trip["created_at"], className="text-muted"),
                            html.Small(
                                f"{t('trip_list.completed', lang=lang)}: {trip.get('completed_at')}",
                                className="d-block",
                                style={"color": "#198754", "fontWeight": "600"},
                            ) if trip.get("completed_at") else None,
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
                        title=t("trip_list.delete_trip", lang=lang),
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


def build_selected_object_items(registry, destination_ids, allow_remove=True, lang="bg"):
    return [
        dbc.ListGroupItem(
            html.Div(
                [component for component in [
                    html.Div(
                        [
                            html.H6(landmark.name, className="mb-1 small"),
                            html.P(landmark.location, className="mb-1 small"),
                        ],
                        style={"flex": "1 1 auto", "minWidth": 0},
                    ),
                    dbc.Button(
                        "X",
                        id={"type": "remove-selected-item", "index": landmark.id},
                        n_clicks=0,
                        color="link",
                        size="sm",
                        title=t("selected_items.remove_monument", lang=lang),
                        style={
                            "color": "#dc3545",
                            "fontWeight": "700",
                            "textDecoration": "none",
                            "flex": "0 0 auto",
                            "padding": "0.1rem 0.25rem",
                        },
                    ) if allow_remove else None,
                ] if component is not None],
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "gap": "0.5rem",
                },
            ),
            className="p-3 selected-monument-item",
            id=f"selected-item-{landmark.id}",
        )
        for landmark in registry.get_landmarks(destination_ids or [])
    ]

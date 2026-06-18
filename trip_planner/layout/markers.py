import dash_bootstrap_components as dbc
from dash import html
import dash_leaflet as dl
from trip_planner.i18n import t


def create_marker(landmark, pin_icon, selected_ids=None, selected_icon=None, lang="bg", allow_add_to_trip=True):
    selected_ids = set(selected_ids or [])
    selected_icon = selected_icon or pin_icon
    is_selected = landmark.id in selected_ids
    return dl.Marker(
        position=[landmark.lat, landmark.lon],
        children=[
            dl.Tooltip(landmark.name),
            dl.Popup(html.Div([
                html.H5(landmark.name),
                html.H6(landmark.location),
                html.A(
                    t("marker.learn_more", lang=lang),
                    href=landmark.link,
                    target="_blank",
                    style={"display": "block", "textAlign": "center"},
                ),
                dbc.Button(
                    t("marker.add_to_trip", lang=lang) if not is_selected else t("marker.in_trip", lang=lang),
                    id={"type": "add-marker-btn", "index": landmark.id},
                    color="success",
                    size="sm",
                    className="mt-2 w-100",
                    disabled=is_selected,
                ) if allow_add_to_trip else None,
            ])),
        ],
        id={"type": "marker", "index": landmark.id},
        icon=selected_icon if is_selected else pin_icon,
    )


def create_markers(landmarks, pin_icon, selected_ids=None, selected_icon=None, lang="bg", allow_add_to_trip=True):
    return [
        create_marker(landmark, pin_icon, selected_ids, selected_icon, lang, allow_add_to_trip)
        for landmark in landmarks
    ]

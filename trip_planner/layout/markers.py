import dash_bootstrap_components as dbc
from dash import html
import dash_leaflet as dl


def create_marker(landmark, pin_icon, selected_ids=None, selected_icon=None):
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
                    "Learn more",
                    href=landmark.link,
                    target="_blank",
                    style={"display": "block", "text-align": "center"},
                ),
                dbc.Button(
                    "Added to trip" if is_selected else "Add to trip",
                    id={"type": "add-marker-btn", "index": landmark.id},
                    color="success",
                    size="sm",
                    className="mt-2 w-100",
                    disabled=is_selected,
                ),
            ])),
        ],
        id={"type": "marker", "index": landmark.id},
        icon=selected_icon if is_selected else pin_icon,
    )


def create_markers(landmarks, pin_icon, selected_ids=None, selected_icon=None):
    return [
        create_marker(landmark, pin_icon, selected_ids, selected_icon)
        for landmark in landmarks
    ]

import dash_bootstrap_components as dbc
from dash import html
import dash_leaflet as dl


def create_markers(landmarks, pin_icon, selected_ids=None, selected_icon=None):
    selected_ids = set(selected_ids or [])
    selected_icon = selected_icon or pin_icon
    return [
        dl.Marker(
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
                        "Added to trip" if landmark.id in selected_ids else "Add to trip",
                        id={"type": "add-marker-btn", "index": landmark.id},
                        color="success",
                        size="sm",
                        className="mt-2 w-100",
                        disabled=landmark.id in selected_ids,
                    ),
                ])),
            ],
            id={"type": "marker", "index": landmark.id},
            icon=selected_icon if landmark.id in selected_ids else pin_icon,
        )
        for landmark in landmarks
    ]

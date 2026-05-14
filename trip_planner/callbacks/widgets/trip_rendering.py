from dash import html
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from backend.tsp_formulas import fetch_route_steps
from callbacks.utils.routing import location_tuple
from callbacks.utils.trip_state import (
    active_route_leg_index,
    next_action_stop_index,
    trip_complete,
)
from styles import current_point_icon, grayed_number_icon, house_icon, number_icon


def build_trip_content(registry, active_trip):
    """Returns (trip_markers, polylines) for a given active_trip dict."""
    stop_ids = active_trip["visit_order"]
    visited = set(active_trip["visited_indices"])
    custom_start = active_trip.get("custom_start_location")
    custom_end = active_trip.get("custom_end_location")

    result = fetch_route_steps(
        registry.get_landmarks(stop_ids),
        start_point=location_tuple(custom_start),
        end_point=location_tuple(custom_end),
    )
    active_leg_idx = active_route_leg_index(active_trip)
    is_trip_complete = trip_complete(active_trip)
    next_action_idx = next_action_stop_index(active_trip)
    passed_coords = []
    current_coords = []
    remaining_coords = []
    full_trip_coords = [coord for segment in result.segments for coord in segment]
    for i, segment in enumerate(result.segments):
        if is_trip_complete or (active_leg_idx is not None and i < active_leg_idx):
            passed_coords.extend(segment)
        elif active_leg_idx is not None and i == active_leg_idx:
            current_coords.extend(segment)
        else:
            remaining_coords.extend(segment)

    status_polylines = []
    if passed_coords:
        status_polylines.append(dl.Polyline(
            id="trip-passed-polyline",
            positions=passed_coords,
            color="#888888",
            weight=9,
            opacity=0.6,
        ))
    if remaining_coords:
        status_polylines.append(dl.Polyline(
            id="trip-remaining-polyline",
            positions=remaining_coords,
            color="#333333",
            weight=10,
        ))
    if current_coords:
        status_polylines.append(dl.Polyline(
            id="trip-current-polyline",
            positions=current_coords,
            color="#1a6fcf",
            weight=9,
        ))
    overview_polylines = []
    if full_trip_coords:
        overview_polylines.append(dl.Polyline(
            id="trip-overview-polyline",
            positions=full_trip_coords,
            color="white",
            weight=2,
            dashArray="10 16",
            interactive=False,
        ))

    markers = []
    saved_location_markers = []
    if custom_start:
        saved_location_markers.append(
            dl.Marker(
                position=[custom_start["lat"], custom_start["lon"]],
                icon=house_icon(),
                interactive=False,
                children=[dl.Tooltip("Start location")],
            )
        )
    if custom_end:
        end_index = len(stop_ids)
        if end_index in visited:
            popup_extra = html.Div(
                "\u2713 Visited",
                style={"textAlign": "center", "color": "#9e9e9e", "marginTop": "0.5rem"},
            )
        elif end_index == next_action_idx:
            popup_extra = dbc.Button(
                "Visited",
                id={"type": "visit-btn", "index": end_index},
                color="success",
                size="sm",
                className="mt-2 w-100",
            )
        else:
            popup_extra = dbc.Button(
                "Visited",
                id={"type": "visit-btn", "index": end_index},
                color="success",
                size="sm",
                className="mt-2 w-100",
                disabled=True,
            )
        saved_location_markers.append(
            dl.Marker(
                position=[custom_end["lat"], custom_end["lon"]],
                icon=house_icon(),
                children=[
                    dl.Tooltip("End point"),
                    dl.Popup(html.Div([
                        html.H5("End point"),
                        html.Div(
                            "Mark this stop visited to complete your trip.",
                            className="text-muted",
                            style={"fontSize": "0.95rem"},
                        ),
                        popup_extra,
                    ])),
                ],
            )
        )

    display_num = 0
    for i, landmark_id in enumerate(stop_ids):
        landmark = registry.get_landmark(landmark_id)
        if not landmark:
            continue
        display_num += 1
        if i in visited:
            icon = grayed_number_icon(display_num)
            popup_extra = html.Div(
                "\u2713 Visited",
                style={"textAlign": "center", "color": "#9e9e9e", "marginTop": "0.5rem"},
            )
        elif i == next_action_idx:
            icon = current_point_icon(display_num)
            popup_extra = dbc.Button(
                "Visited",
                id={"type": "visit-btn", "index": i},
                color="success",
                size="sm",
                className="mt-2 w-100",
            )
        else:
            icon = number_icon(display_num)
            popup_extra = dbc.Button(
                "Visited",
                id={"type": "visit-btn", "index": i},
                color="success",
                size="sm",
                className="mt-2 w-100",
                disabled=True,
            )
        markers.append(
            dl.Marker(
                position=[landmark.lat, landmark.lon],
                id={"type": "route-marker", "index": i, "landmark_id": landmark.id},
                icon=icon,
                children=[
                    dl.Tooltip(landmark.name),
                    dl.Popup(html.Div([
                        html.H5(landmark.name),
                        html.H6(landmark.location),
                        html.A(
                            "Learn more",
                            href=landmark.link,
                            target="_blank",
                            style={"display": "block", "textAlign": "center"},
                        ),
                        popup_extra,
                    ])),
                ],
            )
        )
    return saved_location_markers + markers, status_polylines, overview_polylines

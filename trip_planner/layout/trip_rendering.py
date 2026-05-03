from dash import html
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from backend.tsp_formulas import fetch_route_steps
from utils.routing import location_tuple
from utils.trip_state import (
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
    passed_coords = []
    current_coords = []
    remaining_coords = []
    all_coords = []
    for i, segment in enumerate(result.segments):
        all_coords.extend(segment)
        if is_trip_complete or (active_leg_idx is not None and i < active_leg_idx):
            passed_coords.extend(segment)
        elif active_leg_idx is not None and i == active_leg_idx:
            current_coords.extend(segment)
        else:
            remaining_coords.extend(segment)

    polylines = []
    if passed_coords:
        polylines.append(html.Div(dl.Polyline(
            positions=passed_coords, color="#888888", weight=9, opacity=0.6,
        )))
    unvisited_coords = current_coords + remaining_coords
    if unvisited_coords:
        polylines.append(html.Div(dl.Polyline(
            positions=unvisited_coords, color="#333333", weight=10,
        )))
    if current_coords:
        polylines.append(html.Div(dl.Polyline(
            positions=current_coords, color="#1a6fcf", weight=9,
        )))
    if all_coords:
        polylines.append(html.Div(dl.Polyline(
            positions=all_coords, color="white", weight=2, dashArray="10 16",
        )))

    markers = []
    saved_location_markers = []
    saved_locations = []
    if custom_start:
        saved_locations.append(("Start location", custom_start))
    if custom_end:
        saved_locations.append(("End location", custom_end))

    grouped_locations = {}
    for label, location in saved_locations:
        key = (round(location["lat"], 7), round(location["lon"], 7))
        grouped_locations.setdefault(key, {"labels": [], "location": location})
        grouped_locations[key]["labels"].append(label)

    for item in grouped_locations.values():
        location = item["location"]
        label = " / ".join(item["labels"])
        saved_location_markers.append(
            dl.Marker(
                position=[location["lat"], location["lon"]],
                icon=house_icon(),
                interactive=False,
                children=[dl.Tooltip(label)],
            )
        )

    next_action_idx = next_action_stop_index(active_trip)
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
    return saved_location_markers + markers, polylines

from dash import html
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from services.trip_route import TripRoute
from services.trip_optimization import fetch_route_steps
from callbacks.utils.routing import decode_route_polyline, location_tuple
from callbacks.widgets.access_connectors import build_access_connector_polylines
from i18n import t
from styles import current_point_icon, grayed_number_icon, house_icon, number_icon


def build_trip_content(registry, active_trip, lang="bg"):
    """Returns (trip_markers, polylines) for a given active_trip dict."""
    stop_ids = active_trip.get("visit_order") or []
    trip_route = TripRoute.from_store(active_trip)
    visited = trip_route.visited_indices
    custom_start = active_trip.get("custom_start_location")
    custom_end = active_trip.get("custom_end_location")

    landmarks = registry.landmarks_by_ids(stop_ids)
    route_legs = active_trip.get("route_legs") or []
    route_segments = [
        decode_route_polyline(leg.get("polyline"))
        for leg in route_legs
        if leg.get("polyline")
    ]
    if not route_segments:
        result = fetch_route_steps(
            landmarks,
            start_point=location_tuple(custom_start),
            end_point=location_tuple(custom_end),
        )
        route_segments = [decode_route_polyline(leg.polyline) for leg in result.legs]

    active_leg_idx = trip_route.active_leg_index()
    is_trip_complete = trip_route.is_complete
    next_action_idx = trip_route.next_action_index()
    passed_coords = []
    current_coords = []
    remaining_coords = []
    full_trip_coords = [coord for segment in route_segments for coord in segment]
    for i, segment in enumerate(route_segments):
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
    status_polylines.extend(
        build_access_connector_polylines(
            landmarks,
            id_prefix="trip-access-connector",
        )
    )
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
                children=[dl.Tooltip(t("trip_markers.start_location", lang=lang))],
            )
        )
    if custom_end:
        end_index = len(stop_ids)
        if end_index in visited:
            popup_extra = html.Div(
                t("trip_markers.visited_check", lang=lang),
                style={"textAlign": "center", "color": "#9e9e9e", "marginTop": "0.5rem"},
            )
        elif end_index == next_action_idx:
            popup_extra = dbc.Button(
                t("trip_markers.visited", lang=lang),
                id={"type": "visit-btn", "index": end_index},
                color="success",
                size="sm",
                className="mt-2 w-100",
            )
        else:
            popup_extra = dbc.Button(
                t("trip_markers.visited", lang=lang),
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
                    dl.Tooltip(t("trip_markers.end_point", lang=lang)),
                    dl.Popup(html.Div([
                        html.H5(t("trip_markers.end_point", lang=lang)),
                        html.Div(
                            t("trip_markers.mark_end_visited", lang=lang),
                            className="text-muted",
                            style={"fontSize": "0.95rem"},
                        ) if end_index not in visited else None,
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
                t("trip_markers.visited_check", lang=lang),
                style={"textAlign": "center", "color": "#9e9e9e", "marginTop": "0.5rem"},
            )
        elif i == next_action_idx:
            icon = current_point_icon(display_num)
            popup_extra = dbc.Button(
                t("trip_markers.visited", lang=lang),
                id={"type": "visit-btn", "index": i},
                color="success",
                size="sm",
                className="mt-2 w-100",
            )
        else:
            icon = number_icon(display_num)
            popup_extra = dbc.Button(
                t("trip_markers.visited", lang=lang),
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
                            t("marker.learn_more", lang=lang),
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

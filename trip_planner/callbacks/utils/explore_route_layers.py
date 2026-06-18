from types import SimpleNamespace

from dash import html
import dash_leaflet as dl
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from trip_planner import ids
from trip_planner.callbacks.utils.routing import decode_route_polyline
from trip_planner.callbacks.widgets.access_connectors import build_access_connector_polylines
from trip_planner.i18n import t
from trip_planner.services.trip_route import TripRoute
from trip_planner.styles import number_icon


def build_explore_route_layers(registry, trip_data, lang="bg"):
    store = TripRoute.handle_trip_store(trip_data)
    visit_order_ids = store["visit_order"]
    route_legs = store["route_legs"]
    custom_start = store["custom_start_location"]
    custom_end = store["custom_end_location"]

    route_segments = [
        segment
        for segment in (decode_route_polyline(leg.get("polyline")) for leg in route_legs)
        if segment
    ]
    colormap = cm.get_cmap("viridis", len(route_segments) or 1)
    colors = [mcolors.to_hex(colormap(i)) for i in range(len(route_segments))]
    polylines = [
        dl.Polyline(
            id=f"planned-route-segment-{index}",
            positions=segment,
            color=color,
            weight=5,
            pane=ids.PLANNED_TRIP_ROUTE_PANE,
        )
        for index, (segment, color) in enumerate(zip(route_segments, colors))
    ]

    route_points = []
    if custom_start:
        route_points.append(SimpleNamespace(
            id=-1,
            name=t("route.my_location", lang=lang),
            location="",
            lat=custom_start["lat"],
            lon=custom_start["lon"],
            link=None,
        ))
    for landmark_id in visit_order_ids:
        landmark = registry.get_landmark(landmark_id)
        if landmark:
            route_points.append(landmark)
    if custom_end:
        route_points.append(SimpleNamespace(
            id=-1,
            name=t("route.my_location", lang=lang),
            location="",
            lat=custom_end["lat"],
            lon=custom_end["lon"],
            link=None,
        ))

    access_connectors = build_access_connector_polylines(
        (lm for lm in route_points if lm.id != -1),
        id_prefix="planned-access-connector",
        pane=ids.PLANNED_TRIP_ROUTE_PANE,
    )
    route_lines = polylines + access_connectors

    tour_markers = []
    for i, lm in enumerate(route_points):
        marker_number = i if custom_start else i + 1
        marker_props = {}
        if lm.id != -1:
            marker_props["id"] = {"type": "route-marker", "index": i, "landmark_id": lm.id}
        tour_markers.append(
            dl.Marker(
                position=[lm.lat, lm.lon],
                children=[
                    dl.Tooltip(lm.name),
                    dl.Popup(html.Div([
                        html.H5(lm.name),
                        html.H6(lm.location),
                        html.A(
                            t("marker.learn_more", lang=lang),
                            href=lm.link,
                            target="_blank",
                            style={"display": "block", "text-align": "center"},
                        ) if lm.link else None,
                    ])),
                ],
                icon=number_icon(marker_number),
                **marker_props,
            )
        )

    distance_m = trip_data.get("total_distance_m") or 0
    duration_s = trip_data.get("total_duration_s") or 0
    distance_km = distance_m / 1000
    hours, remainder = divmod(int(duration_s), 3600)
    minutes = remainder // 60
    duration_str = f"{hours}h {minutes}min" if hours else f"{minutes} min"
    stats_content = [
        html.Div([html.B(f"{t('route.distance', lang=lang)}: "), f"{distance_km:.1f} km"]),
        html.Div([html.B(f"{t('route.travel_time', lang=lang)}: "), duration_str]),
    ]
    stats_style = {
        "display": "block",
        "position": "absolute",
        "bottom": "1.5rem",
        "left": "1rem",
        "zIndex": 1000,
        "background": "rgba(255,255,255,0.92)",
        "borderRadius": "0.375rem",
        "padding": "0.5rem 0.75rem",
        "boxShadow": "0 1px 5px rgba(0,0,0,0.3)",
        "fontSize": "0.85rem",
        "lineHeight": "1.6",
        "pointerEvents": "none",
    }
    return {
        "polylines": route_lines,
        "tour_markers": tour_markers,
        "stats_content": stats_content,
        "stats_style": stats_style,
    }

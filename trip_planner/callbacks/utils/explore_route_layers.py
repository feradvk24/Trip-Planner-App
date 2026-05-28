from types import SimpleNamespace

from dash import html
import dash_leaflet as dl
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from callbacks.utils import trip_state
from callbacks.utils.routing import decode_route_polyline
from callbacks.widgets.access_connectors import build_access_connector_polylines
from i18n import t
from styles import number_icon


def build_explore_route_layers(registry, trip_data, lang="bg"):
    visit_order_ids = trip_data.get("visit_order") or []
    route_legs = trip_data.get("route_legs") or []

    route_segments = [
        segment
        for segment in (decode_route_polyline(leg.get("polyline")) for leg in route_legs)
        if segment
    ]
    colormap = cm.get_cmap("viridis", len(route_segments) or 1)
    colors = [mcolors.to_hex(colormap(i)) for i in range(len(route_segments))]
    polylines = [
        html.Div(dl.Polyline(positions=segment, color=color, weight=5))
        for segment, color in zip(route_segments, colors)
    ]

    visit_order = []
    for index, landmark_id in enumerate(visit_order_ids):
        if landmark_id == -1:
            if index == 0:
                location = trip_data.get("custom_start_location")
            else:
                location = trip_data.get("custom_end_location")
            if location:
                visit_order.append(SimpleNamespace(
                    id=-1,
                    name=t("route.my_location", lang=lang),
                    location="",
                    lat=location["lat"],
                    lon=location["lon"],
                    link=None,
                ))
            continue
        landmark = registry.get_landmark(landmark_id)
        if landmark:
            visit_order.append(landmark)

    access_connectors = build_access_connector_polylines(
        (lm for lm in visit_order if lm.id != -1),
        id_prefix="planned-access-connector",
    )
    route_lines = polylines + access_connectors

    start_is_my_location = bool(visit_order_ids and visit_order_ids[0] == -1)
    visit_num = {}
    for i, lm in enumerate(visit_order):
        if lm.id not in visit_num:
            visit_num[lm.id] = i if start_is_my_location else i + 1

    tour_markers = []
    for i, lm in enumerate(visit_order):
        if lm.id not in visit_num:
            continue
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
                icon=number_icon(visit_num[lm.id]),
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

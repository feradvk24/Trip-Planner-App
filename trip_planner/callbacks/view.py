from dash import Input, Output, State, ctx, no_update
import dash_leaflet as dl

import ids
from callbacks.widgets.callback_widgets import build_all_markers
from styles import location_dot_icon


def register_view_callbacks(app, registry):
    @app.callback(
        Output(ids.MODE_STORE, "data"),
        Output(ids.BROWSE_OVERLAY_STORE, "data"),
        Input(ids.MODE_BTN_EXPLORE, "n_clicks"),
        Input(ids.MODE_BTN_TRIP, "n_clicks"),
        Input(ids.MODE_BTN_BROWSE, "n_clicks"),
        Input(ids.LOAD_TRIP_BTN, "n_clicks"),
        Input(ids.BROWSE_CLOSE_BTN, "n_clicks"),
        prevent_initial_call=True,
    )
    def switch_mode(explore_clicks, trip_clicks, browse_clicks, load_trip_clicks, browse_close_clicks):
        if ctx.triggered_id == ids.MODE_BTN_TRIP:
            return "trip", False
        if ctx.triggered_id in (ids.MODE_BTN_BROWSE, ids.LOAD_TRIP_BTN):
            return no_update, True
        if ctx.triggered_id == ids.BROWSE_CLOSE_BTN:
            return no_update, False
        return "explore", False

    @app.callback(
        Output(ids.EXPLORE_PANEL, "style"),
        Output(ids.TRIP_PANEL, "style"),
        Output(ids.BROWSE_PANEL, "style"),
        Output(ids.MODE_BTN_EXPLORE, "active"),
        Output(ids.MODE_BTN_TRIP, "active"),
        Output(ids.MODE_BTN_BROWSE, "active"),
        Input(ids.MODE_STORE, "data"),
        Input(ids.BROWSE_OVERLAY_STORE, "data"),
        prevent_initial_call="initial_duplicate",
    )
    def update_mode_panels(mode, browse_open):
        show = {"display": "flex", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0}
        hide = {"display": "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0}
        if mode == "trip":
            return hide, show, hide, False, not browse_open, bool(browse_open)
        return show, hide, hide, not browse_open, False, bool(browse_open)

    @app.callback(
        Output(ids.BROWSE_OVERLAY, "style"),
        Input(ids.BROWSE_OVERLAY_STORE, "data"),
    )
    def update_browse_overlay(browse_open):
        base_style = {
            "position": "absolute",
            "inset": 0,
            "zIndex": 1000,
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "rgba(248, 249, 250, 0.38)",
            "backdropFilter": "blur(1px)",
            "pointerEvents": "auto",
        }
        if browse_open:
            return {**base_style, "display": "flex"}
        return {**base_style, "display": "none"}

    @app.callback(
        Output(ids.USER_LOCATION_LAYER, "children"),
        Input(ids.GEOLOCATION, "position"),
        prevent_initial_call=True,
    )
    def update_user_location(position):
        if not position:
            return []
        lat, lon = position["lat"], position["lon"]
        accuracy = min(position.get("accuracy", 0), 500)
        return [
            dl.Circle(
                center=[lat, lon],
                radius=accuracy,
                color="#1a6fcf",
                fillColor="#1a6fcf",
                fillOpacity=0.15,
                weight=1,
            ),
            dl.Marker(
                position=[lat, lon],
                icon=location_dot_icon(),
                zIndexOffset=1000,
                children=dl.Tooltip("Your location"),
            ),
        ]

    @app.callback(
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.PLANNED_TRIP_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.PLANNED_TRIP_POLYLINE_LAYER, "children", allow_duplicate=True),
        Output(ids.ROUTE_STATS_PANEL, "children", allow_duplicate=True),
        Output(ids.ROUTE_STATS_PANEL, "style", allow_duplicate=True),
        Input(ids.MODE_STORE, "data"),
        State(ids.EXPLORE_MAP_CACHE, "data"),
        State(ids.DESTINATIONS_LIST, "data"),
        prevent_initial_call="initial_duplicate",
    )
    def sync_explore_layers(mode, explore_cache, destination_ids):
        hidden_stats = {"display": "none"}
        if mode != "explore":
            return [], [], [], [], hidden_stats
        if explore_cache:
            return (
                [],
                explore_cache.get("tour_markers", []),
                explore_cache.get("polylines", []),
                explore_cache.get("stats_content", []),
                explore_cache.get("stats_style", hidden_stats),
            )
        return build_all_markers(registry.landmarks, destination_ids or []), [], [], [], hidden_stats

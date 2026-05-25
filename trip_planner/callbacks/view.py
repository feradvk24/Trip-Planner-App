from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_leaflet as dl
from flask_login import current_user

import ids
from backend.crud import get_user_visited_landmark_ids
from callbacks.utils.explore_route_layers import build_explore_route_layers
from callbacks.utils.get_language import get_language_from_url
from callbacks.widgets.callback_widgets import build_all_markers
from styles import location_dot_icon
from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def get_language_from_path(pathname):
    parts = (pathname or "/").strip("/").split("/")
    if parts and parts[0] in SUPPORTED_LANGUAGES:
        return parts[0]
    return DEFAULT_LANGUAGE


def localized_page_path(pathname, page_path):
    language = get_language_from_path(pathname)
    page_path = "/" + page_path.strip("/")
    if page_path == "/":
        return f"/{language}"
    return f"/{language}{page_path}"

def language_path(pathname, language):
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE

    parts = (pathname or "/").strip("/").split("/")

    if parts and parts[0] in SUPPORTED_LANGUAGES:
        parts = parts[1:]
    elif parts and parts[0] in {"browse", "statistics"}:
        parts = parts[1:]

    path_without_language = "/".join(parts)

    if path_without_language:
        return f"/{language}/{path_without_language}"

    return f"/{language}"


def register_view_callbacks(app, registry):
    @app.callback(
        Output(ids.MODE_STORE, "data"),
        Output("url", "href", allow_duplicate=True),
        Input(ids.MODE_BTN_EXPLORE, "n_clicks"),
        Input(ids.MODE_BTN_TRIP, "n_clicks"),
        Input(ids.MODE_BTN_BROWSE, "n_clicks"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def switch_mode(explore_clicks, trip_clicks, browse_clicks, pathname):
        if not any([explore_clicks, trip_clicks, browse_clicks]):
            raise PreventUpdate
        if ctx.triggered_id == ids.MODE_BTN_TRIP:
            return "trip", no_update
        if ctx.triggered_id == ids.MODE_BTN_BROWSE:
            target_path = localized_page_path(pathname, "/browse")
            if target_path == pathname:
                return no_update, no_update
            return no_update, target_path
        return "explore", no_update
    
    @app.callback(
        Output(ids.EXPLORE_PANEL, "style"),
        Output(ids.TRIP_PANEL, "style"),
        Output(ids.LANDMARK_SEARCH_SHELL, "style"),
        Output(ids.MODE_BTN_EXPLORE, "active"),
        Output(ids.MODE_BTN_TRIP, "active"),
        Output(ids.MODE_BTN_BROWSE, "active"),
        Input(ids.MODE_STORE, "data"),
        prevent_initial_call="initial_duplicate",
    )
    def update_mode_panels(mode):
        show = {"display": "flex", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0}
        hide = {"display": "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0}
        search_show = {"display": "block"}
        search_hide = {"display": "none"}
        if mode == "trip":
            return hide, show, search_hide, False, True, False
        return show, hide, search_show, True, False, False

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
        Output(ids.ALL_MARKERS_LAYER, "children"),
        Output(ids.PLANNED_TRIP_MARKERS_LAYER, "children"),
        Output(ids.PLANNED_TRIP_POLYLINE_LAYER, "children"),
        Output(ids.ROUTE_STATS_PANEL, "children"),
        Output(ids.ROUTE_STATS_PANEL, "style"),
        Input(ids.MODE_STORE, "data"),
        Input(ids.HIDE_VISITED_LANDMARKS_FILTER, "value"),
        Input(ids.OPTIMIZED_TRIP_STORE, "data"),
        Input(ids.DESTINATIONS_LIST, "data"),
        State("url", "href"),
    )
    def sync_explore_layers(mode, hide_visited, optimized_trip, destination_ids, href):
        hidden_stats = {"display": "none"}
        if mode != "explore":
            return [], [], [], [], hidden_stats
        lang = get_language_from_url(href)
        if optimized_trip:
            route_layers = build_explore_route_layers(registry, optimized_trip, lang=lang)
            return (
                [],
                route_layers.get("tour_markers", []),
                route_layers.get("polylines", []),
                route_layers.get("stats_content", []),
                route_layers.get("stats_style", hidden_stats),
            )
        hidden_ids = (
            get_user_visited_landmark_ids(current_user.id)
            if hide_visited and current_user.is_authenticated else
            set()
        )
        return build_all_markers(registry.landmarks, destination_ids or [], hidden_ids, lang=lang), [], [], [], hidden_stats


    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Input(ids.LANGUAGE_RADIO, "value"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def reload_with_selected_language(selected_language, current_path):
        if not selected_language:
            raise PreventUpdate

        new_path = language_path(current_path, selected_language)

        if new_path == current_path:
            raise PreventUpdate

        return new_path

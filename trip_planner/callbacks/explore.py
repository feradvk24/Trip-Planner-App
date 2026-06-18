from dash import ALL, Input, Output, Patch, State, ctx, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from flask_login import current_user

from trip_planner import ids
from trip_planner.backend.db.crud import get_user_visited_landmark_ids
from trip_planner.services.landmark_registry import LandmarkRegistry
from trip_planner.services.trip_route import TripRoute
from trip_planner.services.trip_workflows import save_optimized_trip_for_user
from trip_planner.callbacks.utils.get_language import get_language_from_url
from trip_planner.callbacks.utils.routing import resolve_endpoint
from trip_planner.callbacks.widgets.callback_widgets import (
    build_all_markers,
    build_selected_object_items,
    optimize_route_button_children,
)
from trip_planner.i18n import t
from trip_planner.layout.markers import create_marker
from trip_planner.dash_store_schemas.stores import OptimizedTripStore
from trip_planner.styles import checkbox_icon, pin_icon


CLEAR_ALL_STYLE = {
    "fontSize": "0.75rem",
    "color": "#dc3545",
    "cursor": "pointer",
    "userSelect": "none",
    "alignSelf": "center",
}


def register_explore_callbacks(app):
    registry = LandmarkRegistry.get_landmarks()

    def hidden_visited_landmark_ids(hide_visited):
        if not hide_visited or not current_user.is_authenticated:
            return set()
        return get_user_visited_landmark_ids(current_user.id)

    def marker_index_for_landmark(landmark_id, hidden_ids):
        visible_index = 0
        for landmark in registry.landmarks:
            if landmark.id in hidden_ids:
                continue
            if landmark.id == landmark_id:
                return visible_index
            visible_index += 1
        return None

    def patch_marker_selection(landmark_id, selected_ids, hide_visited, lang):
        hidden_ids = hidden_visited_landmark_ids(hide_visited)
        marker_index = marker_index_for_landmark(landmark_id, hidden_ids)
        landmark = registry.get_landmark(landmark_id)
        if marker_index is None or not landmark:
            return no_update

        patched_markers = Patch()
        patched_markers[marker_index] = create_marker(
            landmark,
            pin_icon,
            selected_ids,
            checkbox_icon,
            lang=lang,
        )
        return patched_markers

    @app.callback(
        Output(ids.START_POINT_DROPDOWN, "disabled"),
        Output(ids.END_POINT_DROPDOWN, "disabled"),
        Output(ids.HIDE_VISITED_LANDMARKS_FILTER, "options"),
        Output(ids.LANDMARK_SEARCH_DROPDOWN, "disabled"),
        Output(ids.CLEAR_ALL_BTN, "style"),
        Input(ids.OPTIMIZED_TRIP_STORE, "data"),
        State("url", "href"),
    )
    def sync_route_lock_state(optimized_trip: OptimizedTripStore | None, href):
        route_is_locked = bool(optimized_trip)
        lang = get_language_from_url(href)
        hide_visited_options = [{
            "label": t("sidebar.hide_visited_landmarks", lang=lang),
            "value": "hide_visited",
            "disabled": route_is_locked,
        }]
        clear_all_style = {
            **CLEAR_ALL_STYLE,
            "display": "none" if route_is_locked else "inline",
        }
        return route_is_locked, route_is_locked, hide_visited_options, route_is_locked, clear_all_style

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Input(ids.MODE_STORE, "data"),
        Input(ids.DESTINATIONS_LIST, "data"),
        Input(ids.OPTIMIZED_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call="initial_duplicate",
    )
    def hydrate_selected_objects(mode, destination_ids, optimized_trip: OptimizedTripStore | None, href):
        if mode != "explore":
            raise PreventUpdate
        lang = get_language_from_url(href)
        return build_selected_object_items(
            registry,
            destination_ids or [],
            allow_remove=not bool(optimized_trip),
            lang=lang,
        )

    @app.callback(
        Output(ids.WARN_MODAL, "is_open"),
        Input("warn-modal-close", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_warn_modal(n_clicks):
        return False

    @app.callback(
        Output(ids.WARN_MODAL, "is_open", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data"),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State(ids.OPTIMIZED_TRIP_STORE, "data"),
        State(ids.GEOLOCATION, "position"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def compute_route(
        n_clicks,
        destination_ids,
        start_point_id,
        end_point_id,
        optimized_trip: OptimizedTripStore | None,
        position,
        href,
    ):
        if optimized_trip:
            raise PreventUpdate
        if not destination_ids or len(destination_ids) < 2:
            return True, no_update
        landmarks = registry.landmarks_by_ids(destination_ids)
        start_landmark = resolve_endpoint(registry, start_point_id, position)
        end_landmark = resolve_endpoint(registry, end_point_id, position)
        optimized_trip_data = TripRoute.optimized(
            landmarks,
            start_point=start_landmark,
            end_point=end_landmark,
        ).to_store_dict()

        return False, optimized_trip_data
    

    @app.callback(
        Output(ids.SUCCESS_TOAST, "is_open"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline"),
        Output(ids.SAVE_TRIP_BTN, "disabled"),
        Output(ids.SAVE_TRIP_BTN, "color"),
        Output(ids.SAVE_TRIP_BTN, "style"),
        Input(ids.OPTIMIZED_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call="initial_duplicate",
        running=[
            (Output(ids.OPTIMIZE_ROUTE_BTN, "disabled"), True, False),
            (
                Output(ids.ROUTE_LOADING_OVERLAY, "style"),
                {
                    "display": "flex",
                    "position": "absolute",
                    "inset": 0,
                    "zIndex": 2000,
                    "alignItems": "center",
                    "justifyContent": "center",
                    "background": "rgba(255,255,255,0.38)",
                    "pointerEvents": "none",
                },
                {
                    "display": "none",
                    "position": "absolute",
                    "inset": 0,
                    "zIndex": 2000,
                    "alignItems": "center",
                    "justifyContent": "center",
                    "background": "rgba(255,255,255,0.38)",
                    "pointerEvents": "none",
                },
            ),
        ],
    )
    def render_route(trip_data: OptimizedTripStore | None, href):
        if not trip_data:
            raise PreventUpdate
        lang = get_language_from_url(href)
        return (
            True,
            optimize_route_button_children(t("route.modify_route", lang=lang), is_modify=True),
            "success",
            True,
            False,
            "info",
            {"flex": "1"},
        )

    @app.callback(
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data", allow_duplicate=True),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.OPTIMIZED_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def modify_route(n_clicks, optimized_trip: OptimizedTripStore | None, href):
        lang = get_language_from_url(href)
        if not optimized_trip:
            raise PreventUpdate
        return (
            optimize_route_button_children(t("sidebar.optimize_route", lang=lang)),
            "success",
            False,
            True,
            "secondary",
            {"opacity": "0.45", "flex": "1"},
            None,
        )

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children"),
        Output(ids.DESTINATIONS_LIST, "data"),
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Input({"type": "marker", "index": ALL}, "n_dblclicks"),
        Input({"type": "add-marker-btn", "index": ALL}, "n_clicks"),
        Input({"type": "search-add-marker-btn", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.HIDE_VISITED_LANDMARKS_FILTER, "value"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def add_marker_to_trip(dblclicks_list, add_clicks_list, search_add_clicks_list, selected, hide_visited, href):
        if not ctx.triggered_id or not (any(dblclicks_list) or any(add_clicks_list) or any(search_add_clicks_list)):
            raise PreventUpdate
        if selected is None:
            selected = []

        landmark_id = ctx.triggered_id["index"]
        if landmark_id in selected:
            raise PreventUpdate
        landmark = registry.get_landmark(landmark_id)
        if not landmark:
            raise PreventUpdate
        updated_selection = [*selected, landmark_id]
        lang = get_language_from_url(href)

        return (
            build_selected_object_items(registry, updated_selection, lang=lang),
            updated_selection,
            patch_marker_selection(landmark_id, updated_selection, hide_visited, lang),
        )

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Input({"type": "remove-selected-item", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.HIDE_VISITED_LANDMARKS_FILTER, "value"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def remove_marker_from_trip(remove_clicks_list, selected, hide_visited, href):
        if not ctx.triggered_id or not any(remove_clicks_list):
            raise PreventUpdate
        selected = selected or []
        landmark_id = ctx.triggered_id["index"]
        updated_selection = [selected_id for selected_id in selected if selected_id != landmark_id]
        lang = get_language_from_url(href)

        return (
            build_selected_object_items(registry, updated_selection, lang=lang),
            updated_selection,
            patch_marker_selection(landmark_id, updated_selection, hide_visited, lang),
        )

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        State(ids.HIDE_VISITED_LANDMARKS_FILTER, "value"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def clear_all(n_clicks, hide_visited, href):
        lang = get_language_from_url(href)
        hidden_ids = hidden_visited_landmark_ids(hide_visited)
        return (
            [],
            [],
            build_all_markers(registry.landmarks, [], hidden_ids, lang=lang),
            optimize_route_button_children(t("sidebar.optimize_route", lang=lang)),
            "success",
            False,
            True,
            "secondary",
            {"opacity": "0.45", "flex": "1"},
            None,
        )

    @app.callback(
        Output(ids.START_POINT_DROPDOWN, "options"),
        Output(ids.END_POINT_DROPDOWN, "options"),
        Output(ids.START_POINT_DROPDOWN, "value"),
        Output(ids.END_POINT_DROPDOWN, "value"),
        Input(ids.DESTINATIONS_LIST, "data"),
        Input(ids.GEOLOCATION, "position"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def update_dropdown_options(destination_ids, position, start_point_id, end_point_id, href):
        lang = get_language_from_url(href)
        landmarks = registry.landmarks_by_ids(destination_ids or [])
        auto_option = {"label": t("sidebar.auto", lang=lang), "value": "auto"}
        base_options = [auto_option]
        if position:
            base_options.append({"label": t("route.my_location", lang=lang), "value": "my_location"})
        options = base_options + [{"label": l.name, "value": str(l.id)} for l in landmarks]
        option_values = {option["value"] for option in options}
        start_point_value = start_point_id if start_point_id in option_values else "auto"
        end_point_value = end_point_id if end_point_id in option_values else "auto"
        return options, options, start_point_value, end_point_value

    @app.callback(
        Output(ids.SAVE_TRIP_MODAL, "is_open"),
        Output(ids.SAVE_TRIP_NAME_INPUT, "value"),
        Input(ids.SAVE_TRIP_BTN, "n_clicks"),
        Input("save-trip-cancel-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_save_modal(open_clicks, cancel_clicks):
        if ctx.triggered_id == ids.SAVE_TRIP_BTN:
            return True, ""
        return False, no_update

    @app.callback(
        Output(ids.SAVE_TRIP_MODAL, "is_open", allow_duplicate=True),
        Output(ids.SAVE_TRIP_ALERT, "children"),
        Output(ids.SAVE_TRIP_ALERT, "is_open"),
        Input(ids.SAVE_TRIP_CONFIRM_BTN, "n_clicks"),
        State(ids.SAVE_TRIP_NAME_INPUT, "value"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.OPTIMIZED_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def confirm_save_trip(n_clicks, name, landmark_ids, optimized_trip: OptimizedTripStore | None, href):
        lang = get_language_from_url(href)
        result = save_optimized_trip_for_user(
            current_user.id,
            name,
            landmark_ids,
            optimized_trip,
        )
        if result.ok:
            return False, "", False

        if result.code == "missing_name":
            return True, t("save_trip_modal.enter_name", lang=lang), True
        if result.code == "name_exists":
            return True, t("save_trip_modal.name_exists", lang=lang), True
        if result.code == "missing_route":
            return True, t("warn_modal.message", lang=lang), True
        return True, f"{t('save_trip_modal.failed', lang=lang)}: {result.error}", True

    @app.callback(
        Output(ids.LANDMARK_SEARCH_DROPDOWN, "options"),
        Input(ids.LANDMARK_SEARCH_DROPDOWN, "search_value"),
        Input(ids.HIDE_VISITED_LANDMARKS_FILTER, "value"),
    )
    def update_search_options(search_value, hide_visited):
        query = " ".join((search_value or "").casefold().split())
        if len(query) < 3:
            return []

        query_terms = query.split()
        hidden_ids = hidden_visited_landmark_ids(hide_visited)
        matching_landmarks = []
        for landmark in registry.landmarks:
            if landmark.id in hidden_ids:
                continue
            searchable_text = " ".join(
                f"{landmark.name} {landmark.location}".casefold().split()
            )
            if all(term in searchable_text for term in query_terms):
                matching_landmarks.append(landmark)

        return [{"label": f"{lm.name} - {lm.location}", "value": lm.id} for lm in matching_landmarks]


    @app.callback(
        Output(ids.ACTIVE_INFO_STORE, "data", allow_duplicate=True),
        Output(ids.MAP, "viewport"),
        Output(ids.SEARCH_POPUP_LAYER, "children"),
        Input(ids.LANDMARK_SEARCH_DROPDOWN, "value"),
        State(ids.DESTINATIONS_LIST, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def select_landmark_from_search(landmark_id, destination_ids, href):
        if landmark_id is None:
            return no_update, no_update, []
        lang = get_language_from_url(href)
        landmark_id = int(landmark_id)
        landmark = registry.get_landmark(landmark_id)
        if not landmark:
            raise PreventUpdate
        is_selected = landmark.id in (destination_ids or [])
        return (
            {"type": "landmark", "content": landmark.id},
            {"center": [landmark.lat, landmark.lon], "zoom": 14, "transition": "setView"},
            [
                dl.Popup(
                    html.Div([
                        html.H5(landmark.name),
                        html.H6(landmark.location),
                        html.A(
                            t("marker.learn_more", lang=lang),
                            href=landmark.link,
                            target="_blank",
                            style={"display": "block", "textAlign": "center"},
                        ),
                        dbc.Button(
                            t("marker.in_trip", lang=lang) if is_selected else t("marker.add_to_trip", lang=lang),
                            id={"type": "search-add-marker-btn", "index": landmark.id},
                            color="success",
                            size="sm",
                            className="mt-2 w-100",
                            disabled=is_selected,
                        ),
                    ]),
                    position=[landmark.lat, landmark.lon],
                )
            ],
        )

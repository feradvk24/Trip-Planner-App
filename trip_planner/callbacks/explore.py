from dash import ALL, Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from types import SimpleNamespace
from flask_login import current_user

import ids
from backend.crud import get_user_visited_landmark_ids, save_trip, user_trip_name_exists
from backend.routing_service import fetch_route_steps, optimize_visit_order
from callbacks.utils.get_language import get_language_from_url
from callbacks.utils.routing import (
    build_route_legs,
    decode_route_polyline,
    location_tuple,
    resolve_endpoint,
)
from callbacks.widgets.callback_widgets import (
    build_selected_object_items,
    button_label_text,
    optimize_route_button_children,
)
from callbacks.widgets.access_connectors import build_access_connector_polylines
from i18n import t
from styles import number_icon


def register_explore_callbacks(app, registry):
    def hidden_visited_landmark_ids(hide_visited):
        if not hide_visited or not current_user.is_authenticated:
            return set()
        return get_user_visited_landmark_ids(current_user.id)

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Input(ids.MODE_STORE, "data"),
        Input(ids.DESTINATIONS_LIST, "data"),
        Input(ids.EXPLORE_MAP_CACHE, "data"),
        State("url", "href"),
        prevent_initial_call="initial_duplicate",
    )
    def hydrate_selected_objects(mode, destination_ids, explore_cache, href):
        if mode != "explore":
            raise PreventUpdate
        lang = get_language_from_url(href)
        return build_selected_object_items(
            registry,
            destination_ids or [],
            allow_remove=not bool(explore_cache),
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
        Output(ids.VISIT_ORDER_STORE, "data"),
        Output(ids.WARN_MODAL, "is_open", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data"),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        State(ids.GEOLOCATION, "position"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def compute_route(n_clicks, destination_ids, start_point_id, end_point_id, btn_label, position, href):
        lang = get_language_from_url(href)
        if button_label_text(btn_label) == t("route.modify_route", lang=lang):
            raise PreventUpdate
        if not destination_ids or len(destination_ids) < 2:
            return no_update, True, no_update
        landmarks = registry.get_landmarks(destination_ids)
        start_landmark = resolve_endpoint(registry, start_point_id, position)
        end_landmark = resolve_endpoint(registry, end_point_id, position)
        visit_order = optimize_visit_order(landmarks, start_point=start_landmark, end_point=end_landmark)
        result = fetch_route_steps(visit_order)

        optimized_trip_data = {
            "visit_order": tuple(lm.id for lm in visit_order),
            "route_legs": build_route_legs(len(visit_order), result),
            "user_location_start": {"lat": position["lat"], "lon": position["lon"]} if start_point_id == "my_location" and position else None,
            "user_location_end": {"lat": position["lat"], "lon": position["lon"]} if end_point_id == "my_location" and position else None,
            "total_distance_m": result.distance_m,
            "total_duration_s": result.duration_s,
        }

        return [l.id for l in visit_order], False, optimized_trip_data
    

    @app.callback(
        Output(ids.SUCCESS_TOAST, "is_open"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline"),
        Output(ids.SAVE_TRIP_BTN, "disabled"),
        Output(ids.SAVE_TRIP_BTN, "color"),
        Output(ids.SAVE_TRIP_BTN, "style"),
        Output(ids.EXPLORE_MAP_CACHE, "data"),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.START_POINT_DROPDOWN, "disabled"),
        Output(ids.END_POINT_DROPDOWN, "disabled"),
        Input(ids.OPTIMIZED_TRIP_STORE, "data"),
        State(ids.DESTINATIONS_LIST, "data"),
        State("url", "href"),
        prevent_initial_call=True,
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
    def render_route(trip_data, destination_ids, href):
        if not trip_data:
            raise PreventUpdate
        lang = get_language_from_url(href)
        visit_order_ids = trip_data.get("visit_order") or []
        route_legs = trip_data.get("route_legs") or []

        route_segments = [decode_route_polyline(leg.get("polyline")) for leg in route_legs]
        colormap = cm.get_cmap("viridis", len(route_segments))
        colors = [mcolors.to_hex(colormap(i)) for i in range(len(route_segments))]
        polylines = [
            html.Div(dl.Polyline(positions=segment, color=color, weight=5))
            for segment, color in zip(route_segments, colors)
        ]

        visit_order = []
        for index, landmark_id in enumerate(visit_order_ids):
            if landmark_id == -1:
                location = (
                    trip_data.get("user_location_start")
                    if index == 0 else
                    trip_data.get("user_location_end")
                )
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

        distance_m = trip_data.get("total_distance_m")
        duration_s =trip_data.get("total_duration_s")
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
        explore_cache = {
            "polylines": route_lines,
            "tour_markers": tour_markers,
            "stats_content": stats_content,
            "stats_style": stats_style,
        }
        return (
            True,
            optimize_route_button_children(t("route.modify_route", lang=lang), is_modify=True),
            "success",
            True,
            False,
            "info",
            {"flex": "1"},
            explore_cache,
            build_selected_object_items(registry, destination_ids, allow_remove=False, lang=lang),
            True,
            True,
        )

    @app.callback(
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.EXPLORE_MAP_CACHE, "data", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.START_POINT_DROPDOWN, "disabled", allow_duplicate=True),
        Output(ids.END_POINT_DROPDOWN, "disabled", allow_duplicate=True),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def modify_route(n_clicks, destination_ids, btn_label, href):
        lang = get_language_from_url(href)
        if button_label_text(btn_label) != t("route.modify_route", lang=lang):
            raise PreventUpdate
        return (
            optimize_route_button_children(t("sidebar.optimize_route", lang=lang)),
            "success",
            False,
            True,
            "secondary",
            {"opacity": "0.45", "flex": "1"},
            None,
            None,
            build_selected_object_items(registry, destination_ids, lang=lang),
            False,
            False,
        )

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children"),
        Output(ids.DESTINATIONS_LIST, "data"),
        Input({"type": "marker", "index": ALL}, "n_dblclicks"),
        Input({"type": "add-marker-btn", "index": ALL}, "n_clicks"),
        Input({"type": "search-add-marker-btn", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def add_marker_to_trip(dblclicks_list, add_clicks_list, search_add_clicks_list, selected, href):
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

        return build_selected_object_items(registry, updated_selection, lang=lang), updated_selection

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Input({"type": "remove-selected-item", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def remove_marker_from_trip(remove_clicks_list, selected, href):
        if not ctx.triggered_id or not any(remove_clicks_list):
            raise PreventUpdate
        selected = selected or []
        landmark_id = ctx.triggered_id["index"]
        updated_selection = [selected_id for selected_id in selected if selected_id != landmark_id]
        lang = get_language_from_url(href)

        return build_selected_object_items(registry, updated_selection, lang=lang), updated_selection

    @app.callback(
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.VISIT_ORDER_STORE, "data", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.EXPLORE_MAP_CACHE, "data", allow_duplicate=True),
        Output(ids.OPTIMIZED_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.START_POINT_DROPDOWN, "disabled", allow_duplicate=True),
        Output(ids.END_POINT_DROPDOWN, "disabled", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def clear_all(n_clicks, href):
        lang = get_language_from_url(href)
        return [], [], [], optimize_route_button_children(t("sidebar.optimize_route", lang=lang)), "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}, None, None, False, False

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
        landmarks = registry.get_landmarks(destination_ids or [])
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
        State(ids.VISIT_ORDER_STORE, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State(ids.GEOLOCATION, "position"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def confirm_save_trip(n_clicks, name, landmark_ids, visit_order, start_value, end_value, position, href):
        lang = get_language_from_url(href)
        if not name or not name.strip():
            return True, t("save_trip_modal.enter_name", lang=lang), True
        trip_name = name.strip()
        if user_trip_name_exists(current_user.id, trip_name):
            return True, t("save_trip_modal.name_exists", lang=lang), True
        saved_user_location = {"lat": position["lat"], "lon": position["lon"]} if position else None
        custom_start_location = saved_user_location if start_value == "my_location" else None
        custom_end_location = saved_user_location if end_value == "my_location" else None
        stop_ids = [lid for lid in (visit_order or []) if lid != -1]
        try:
            route_result = fetch_route_steps(
                registry.get_landmarks(stop_ids),
                start_point=location_tuple(custom_start_location),
                end_point=location_tuple(custom_end_location),
            )
            route_point_count = len(stop_ids) + int(bool(custom_start_location)) + int(bool(custom_end_location))
            save_trip(
                username=current_user.id,
                name=trip_name,
                landmark_ids=landmark_ids or [],
                visit_order=stop_ids,
                route_legs=build_route_legs(route_point_count, route_result),
                custom_start_location=custom_start_location,
                custom_end_location=custom_end_location,
                saved_user_location=saved_user_location,
            )
        except Exception as e:
            return True, f"{t('save_trip_modal.failed', lang=lang)}: {e}", True
        return False, "", False

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
                            style={"display": "block", "text-align": "center"},
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

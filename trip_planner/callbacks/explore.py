from dash import ALL, Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from flask_login import current_user

import ids
from backend.crud import save_trip
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from callbacks.utils.routing import (
    build_route_legs,
    location_tuple,
    resolve_endpoint,
    resolve_visit_order_landmarks,
)
from callbacks.widgets.callback_widgets import (
    build_all_markers,
    button_label_text,
    optimize_route_button_children,
)
from styles import number_icon


def register_explore_callbacks(app, registry):
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
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        State(ids.GEOLOCATION, "position"),
        prevent_initial_call=True,
    )
    def compute_route(n_clicks, destination_ids, start_point_id, end_point_id, btn_label, position):
        if button_label_text(btn_label) == "Modify Route":
            raise PreventUpdate
        if not destination_ids or len(destination_ids) < 2:
            return no_update, True
        landmarks = registry.get_landmarks(destination_ids)
        start_landmark = resolve_endpoint(registry, start_point_id, position)
        end_landmark = resolve_endpoint(registry, end_point_id, position)
        visit_order = solve_tsp(landmarks, start_point=start_landmark, end_point=end_landmark)
        return [lm.id for lm in visit_order], False

    @app.callback(
        Output(ids.PLANNED_TRIP_POLYLINE_LAYER, "children"),
        Output(ids.SUCCESS_TOAST, "is_open"),
        Output(ids.ALL_MARKERS_LAYER, "children"),
        Output(ids.PLANNED_TRIP_MARKERS_LAYER, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline"),
        Output(ids.SAVE_TRIP_BTN, "disabled"),
        Output(ids.SAVE_TRIP_BTN, "color"),
        Output(ids.SAVE_TRIP_BTN, "style"),
        Output(ids.ROUTE_STATS_PANEL, "children"),
        Output(ids.ROUTE_STATS_PANEL, "style"),
        Output(ids.EXPLORE_MAP_CACHE, "data"),
        Input(ids.VISIT_ORDER_STORE, "data"),
        State(ids.GEOLOCATION, "position"),
        prevent_initial_call=True,
        running=[(Output(ids.OPTIMIZE_ROUTE_BTN, "disabled"), True, False)],
    )
    def render_route(visit_order_ids, position):
        if not visit_order_ids:
            raise PreventUpdate
        visit_order = resolve_visit_order_landmarks(registry, visit_order_ids, position=position)

        result = fetch_route_steps(visit_order)
        colormap = cm.get_cmap("viridis", len(result.segments))
        colors = [mcolors.to_hex(colormap(i)) for i in range(len(result.segments))]
        polylines = [
            html.Div(dl.Polyline(positions=segment, color=color, weight=5))
            for segment, color in zip(result.segments, colors)
        ]

        start_is_my_location = visit_order_ids[0] == -1
        visit_num = {}
        for i, lm in enumerate(visit_order):
            if lm.id not in visit_num:
                visit_num[lm.id] = i if start_is_my_location else i + 1

        tour_markers = [
            dl.Marker(
                position=[lm.lat, lm.lon],
                children=[
                    dl.Tooltip(lm.name),
                    dl.Popup(html.Div([
                        html.H5(lm.name),
                        html.H6(lm.location),
                        html.A(
                            "Learn more",
                            href=lm.link,
                            target="_blank",
                            style={"display": "block", "text-align": "center"},
                        ),
                    ])),
                ],
                icon=number_icon(visit_num[lm.id]),
            )
            for lm in visit_order
            if lm.id in visit_num
        ]

        distance_km = result.distance_m / 1000
        hours, remainder = divmod(int(result.duration_s), 3600)
        minutes = remainder // 60
        duration_str = f"{hours}h {minutes}min" if hours else f"{minutes} min"
        stats_content = [
            html.Div([html.B("\U0001f3ce\ufe0f Distance: "), f"{distance_km:.1f} km"]),
            html.Div([html.B("\u23f1\ufe0f Travel time: "), duration_str]),
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
            "polylines": polylines,
            "tour_markers": tour_markers,
            "stats_content": stats_content,
            "stats_style": stats_style,
        }
        return polylines, True, [], tour_markers, optimize_route_button_children("Modify Route"), "success", True, False, "info", {"flex": "1"}, stats_content, stats_style, explore_cache

    @app.callback(
        Output(ids.PLANNED_TRIP_POLYLINE_LAYER, "children", allow_duplicate=True),
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.PLANNED_TRIP_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.ROUTE_STATS_PANEL, "style", allow_duplicate=True),
        Output(ids.EXPLORE_MAP_CACHE, "data", allow_duplicate=True),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        prevent_initial_call=True,
    )
    def modify_route(n_clicks, destination_ids, btn_label):
        if button_label_text(btn_label) != "Modify Route":
            raise PreventUpdate
        return [], build_all_markers(registry.landmarks, destination_ids), [], optimize_route_button_children("Optimize Route"), "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}, {"display": "none"}, None

    @app.callback(
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children"),
        Output(ids.DESTINATIONS_LIST, "data"),
        Input({"type": "marker", "index": ALL}, "n_dblclicks"),
        Input({"type": "add-marker-btn", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.SELECTED_OBJECTS_GROUP, "children"),
        prevent_initial_call=True,
    )
    def add_marker_to_trip(dblclicks_list, add_clicks_list, selected, current_children):
        if not ctx.triggered_id or not (any(dblclicks_list) or any(add_clicks_list)):
            raise PreventUpdate
        if selected is None:
            selected = []
        if current_children is None:
            current_children = []

        landmark_id = ctx.triggered_id["index"]
        if landmark_id in selected:
            raise PreventUpdate
        landmark = registry.get_landmark(landmark_id)
        if not landmark:
            raise PreventUpdate
        selected.append(landmark_id)
        item = dbc.ListGroupItem([
            html.H6(landmark.name, className="mb-1 small"),
            html.P(landmark.location, className="mb-1 small"),
        ], className="p-3", id=f"selected-item-{landmark_id}")
        current_children.append(item)

        return build_all_markers(registry.landmarks, selected), current_children, selected

    @app.callback(
        Output(ids.ALL_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.PLANNED_TRIP_MARKERS_LAYER, "children", allow_duplicate=True),
        Output(ids.PLANNED_TRIP_POLYLINE_LAYER, "children", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Output(ids.ROUTE_STATS_PANEL, "style", allow_duplicate=True),
        Output(ids.EXPLORE_MAP_CACHE, "data", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_all(n_clicks):
        return build_all_markers(registry.landmarks, []), [], [], [], [], optimize_route_button_children("Optimize Route"), "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}, {"display": "none"}, None

    @app.callback(
        Output(ids.START_POINT_DROPDOWN, "options"),
        Output(ids.END_POINT_DROPDOWN, "options"),
        Output(ids.START_POINT_DROPDOWN, "value"),
        Output(ids.END_POINT_DROPDOWN, "value"),
        Input(ids.DESTINATIONS_LIST, "data"),
        Input(ids.GEOLOCATION, "position"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        prevent_initial_call=True,
    )
    def update_dropdown_options(destination_ids, position, start_point_id, end_point_id):
        landmarks = registry.get_landmarks(destination_ids or [])
        auto_option = {"label": "Automatic", "value": "auto"}
        base_options = [auto_option]
        if position:
            base_options.append({"label": "My location", "value": "my_location"})
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
        prevent_initial_call=True,
    )
    def confirm_save_trip(n_clicks, name, landmark_ids, visit_order, start_value, end_value, position):
        if not name or not name.strip():
            return True, "Please enter a trip name.", True
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
                name=name.strip(),
                landmark_ids=landmark_ids or [],
                visit_order=stop_ids,
                route_legs=build_route_legs(route_point_count, route_result),
                custom_start_location=custom_start_location,
                custom_end_location=custom_end_location,
                saved_user_location=saved_user_location,
            )
        except Exception as e:
            return True, f"Failed to save trip: {e}", True
        return False, "", False

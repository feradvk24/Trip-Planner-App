from dash import Output, Input, State, ALL, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import ids
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon, number_icon, location_dot_icon, grayed_number_icon, current_point_icon, house_icon
from marker_config import Landmark
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import dash_leaflet as dl
from flask_login import login_user, current_user
from backend.auth import verify_user, create_user, User
from backend.crud import save_trip, get_user_trips, get_public_trips, delete_trip, update_trip_progress, set_trip_public_status
from components import create_markers


def resolve_endpoint(registry, point_id, position):
    if point_id == "my_location" and position:
        return Landmark(id=-1, name="My location", location="", lat=position["lat"], lon=position["lon"])
    if point_id and point_id != "auto":
        return registry.get_landmark(int(point_id))
    return None


def register_callbacks(app, registry):
    def _button_label_text(children):
        if isinstance(children, str):
            return children
        if isinstance(children, list):
            return "".join(child for child in children if isinstance(child, str)).strip()
        return ""

    def _optimize_route_button_children(label):
        icon_class = "bi bi-pencil-square me-2" if label == "Modify Route" else "bi bi-signpost-split me-2"
        return [html.I(className=icon_class), label]

    def _build_load_trip_items(trips, allow_delete=True, show_owner=False):
        if not trips:
            return [dbc.ListGroupItem("No trips to show...", disabled=True)]
        return [
            dbc.ListGroupItem(
                html.Div(
                    [component for component in [
                        html.Button(
                            [component for component in [
                                html.Div(t["name"], style={"fontWeight": "600"}),
                                html.Small(
                                    f"Shared by {t.get('owner_name') or t.get('owner_username')}",
                                    className="text-muted d-block",
                                ) if show_owner else None,
                                html.Small(t["created_at"], className="text-muted"),
                            ] if component is not None],
                            id={"type": "load-trip-item", "index": t["id"]},
                            n_clicks=0,
                            style={
                                "background": "none",
                                "border": "none",
                                "padding": 0,
                                "textAlign": "left",
                                "flex": "1 1 auto",
                                "minWidth": 0,
                                "cursor": "pointer",
                            },
                        ),
                        dbc.Button(
                            "X",
                            id={"type": "delete-trip-item", "index": t["id"]},
                            n_clicks=0,
                            color="link",
                            size="sm",
                            title="Delete trip",
                            style={
                                "color": "#dc3545",
                                "fontWeight": "700",
                                "textDecoration": "none",
                                "flex": "0 0 auto",
                            },
                        ) if allow_delete else None,
                    ] if component is not None],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "0.75rem",
                    },
                ),
                className="saved-trip-item",
            )
            for t in trips
        ]

    def _build_selected_object_items(destination_ids):
        return [
            dbc.ListGroupItem([
                html.H6(landmark.name, className="mb-1 small"),
                html.P(landmark.location, className="mb-1 small"),
            ], className="p-3", id=f"selected-item-{landmark.id}")
            for landmark in registry.get_landmarks(destination_ids or [])
        ]

    def _sanitize_shared_trip(trip):
        landmark_ids = [lid for lid in (trip.get("landmark_ids") or []) if lid != -1]
        visit_order = [lid for lid in (trip.get("visit_order") or landmark_ids) if lid != -1]
        has_private_endpoint = bool(trip.get("custom_start_location") or trip.get("custom_end_location"))
        return {
            **trip,
            "landmark_ids": landmark_ids,
            "visit_order": visit_order,
            "route_legs": [] if has_private_endpoint else trip.get("route_legs", []),
            "custom_start_location": None,
            "custom_end_location": None,
            "saved_user_location": None,
        }

    def _build_all_markers(destination_ids):
        return create_markers(registry.landmarks, pin_icon, destination_ids, checkbox_icon)

    def _location_tuple(location):
        if not location:
            return None
        return location["lat"], location["lon"]

    def _clamp_stop_index(active_trip):
        stop_ids = active_trip.get("visit_order") or []
        if not stop_ids:
            return 0
        return max(0, min(active_trip.get("current_point_index", 0), len(stop_ids) - 1))

    def _trip_complete(active_trip):
        stop_ids = active_trip.get("visit_order") or []
        visited = set(active_trip.get("visited_indices") or [])
        return bool(stop_ids) and all(i in visited for i in range(len(stop_ids)))

    def _next_action_stop_index(active_trip):
        stop_ids = active_trip.get("visit_order") or []
        if not stop_ids or _trip_complete(active_trip):
            return None
        visited = set(active_trip.get("visited_indices") or [])
        return next((i for i in range(len(stop_ids)) if i not in visited), None)

    def _active_route_leg_index(active_trip):
        next_idx = _next_action_stop_index(active_trip)
        if next_idx is None:
            return None
        start_offset = 1 if active_trip.get("custom_start_location") else 0
        return max(0, start_offset + next_idx - 1)

    def _resolve_visit_order_landmarks(visit_order_ids, position=None):
        visit_order_lms = []
        for lid in visit_order_ids or []:
            if lid == -1:
                if position:
                    visit_order_lms.append(Landmark(id=-1, name="My location", location="", lat=position["lat"], lon=position["lon"]))
                continue
            lm = registry.get_landmark(lid)
            if lm:
                visit_order_lms.append(lm)
        return visit_order_lms

    def _build_route_legs(route_point_count, route_result):
        # Indexes refer to the composed route:
        # [custom_start?] + visit_order landmarks + [custom_end?].
        return [
            {
                "from_index": i,
                "to_index": i + 1,
                "distance_m": leg.get("distance_m", 0),
                "duration_s": leg.get("duration_s", 0),
            }
            for i, leg in enumerate(route_result.legs)
            if i + 1 < route_point_count
        ]

    def _format_distance(distance_m):
        if distance_m is None:
            return "Unknown"
        if distance_m >= 1000:
            return f"{distance_m / 1000:.1f} km"
        return f"{int(round(distance_m))} m"

    def _trip_point_summary(visit_order_ids, index):
        if index < 0 or index >= len(visit_order_ids):
            return None
        landmark_id = visit_order_ids[index]
        if landmark_id == -1:
            return {"name": "My location", "location": ""}
        landmark = registry.get_landmark(landmark_id)
        if not landmark:
            return {"name": "Unknown destination", "location": ""}
        return {"name": landmark.name, "location": landmark.location}

    def _get_route_legs(active_trip, position=None):
        route_legs = active_trip.get("route_legs") or []
        if route_legs:
            return route_legs
        stop_ids = active_trip.get("visit_order") or []
        custom_start = active_trip.get("custom_start_location")
        custom_end = active_trip.get("custom_end_location")
        try:
            route_result = fetch_route_steps(
                registry.get_landmarks(stop_ids),
                start_point=_location_tuple(custom_start),
                end_point=_location_tuple(custom_end),
            )
            route_point_count = len(stop_ids) + int(bool(custom_start)) + int(bool(custom_end))
            return _build_route_legs(route_point_count, route_result)
        except Exception:
            return []

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
        if _button_label_text(btn_label) == "Modify Route":
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
        visit_order = _resolve_visit_order_landmarks(visit_order_ids, position=position)

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
                        html.A("Learn more", href=lm.link, target="_blank",
                               style={"display": "block", "text-align": "center"})
                    ]))
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
        return polylines, True, [], tour_markers, _optimize_route_button_children("Modify Route"), "success", True, False, "info", {"flex": "1"}, stats_content, stats_style, explore_cache

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
        if _button_label_text(btn_label) != "Modify Route":
            raise PreventUpdate
        return [], _build_all_markers(destination_ids), [], _optimize_route_button_children("Optimize Route"), "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}, {"display": "none"}, None

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

        return _build_all_markers(selected), current_children, selected

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
        return _build_all_markers([]), [], [], [], [], _optimize_route_button_children("Optimize Route"), "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}, {"display": "none"}, None

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
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children"),
        Output(ids.LOGIN_ALERT, "is_open"),
        Input(ids.LOGIN_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        prevent_initial_call=True,
    )
    def handle_login(n_clicks, username, password):
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if verify_user(username, password):
            login_user(User(username))
            return "/", "", False
        return no_update, "Invalid username or password.", True

    @app.callback(
        Output(ids.REGISTER_FIELDS, "style"),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.REGISTER_FIELDS, "style"),
        prevent_initial_call=True,
    )
    def toggle_register_fields(n_clicks, current_style):
        if current_style and current_style.get("display") == "none":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "is_open", allow_duplicate=True),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        State(ids.REGISTER_FIRST_NAME, "value"),
        State(ids.REGISTER_LAST_NAME, "value"),
        State(ids.REGISTER_FIELDS, "style"),
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, username, password, first_name, last_name, fields_style):
        if fields_style and fields_style.get("display") == "none":
            raise PreventUpdate
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if not first_name or not first_name.strip():
            return no_update, "Please enter your first name.", True
        if not last_name or not last_name.strip():
            return no_update, "Please enter your last name.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        if create_user(username, password, first_name.strip(), last_name.strip()):
            login_user(User(username))
            return "/", "", False
        return no_update, "Username already exists.", True

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Input(ids.LOGOUT_BUTTON, "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_logout(n_clicks):
        from flask_login import logout_user as _logout
        _logout()
        return "/login"

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
                start_point=_location_tuple(custom_start_location),
                end_point=_location_tuple(custom_end_location),
            )
            route_point_count = len(stop_ids) + int(bool(custom_start_location)) + int(bool(custom_end_location))
            save_trip(
                username=current_user.id,
                name=name.strip(),
                landmark_ids=landmark_ids or [],
                visit_order=stop_ids,
                route_legs=_build_route_legs(route_point_count, route_result),
                custom_start_location=custom_start_location,
                custom_end_location=custom_end_location,
                saved_user_location=saved_user_location,
            )
        except Exception as e:
            return True, f"Failed to save trip: {e}", True
        return False, "", False

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
        Output(ids.LOAD_TRIP_LIST, "children"),
        Output(ids.USER_SHARED_TRIPS_LIST, "children"),
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.BROWSE_SAVED_TRIPS_STORE, "data"),
        Output(ids.BROWSE_SHARED_TRIPS_STORE, "data"),
        Input(ids.BROWSE_OVERLAY_STORE, "data"),
        Input(ids.BROWSE_TABS, "active_tab"),
        Input({"type": "delete-trip-item", "index": ALL}, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def refresh_browse_saved_trips(browse_open, active_tab, delete_clicks_list, active_trip):
        active_trip_data = no_update
        if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "delete-trip-item":
            trip_id = ctx.triggered_id["index"]
            delete_trip(current_user.id, trip_id)
            if active_trip and active_trip.get("trip_id") == trip_id:
                active_trip_data = None
            trips = get_user_trips(current_user.id)
            return _build_load_trip_items(trips), no_update, active_trip_data, trips, no_update

        if not browse_open:
            raise PreventUpdate

        if active_tab == "my-saved-trips":
            trips = get_user_trips(current_user.id)
            return _build_load_trip_items(trips), no_update, active_trip_data, trips, no_update

        if active_tab == "user-shared-trips":
            trips = [
                _sanitize_shared_trip(trip) for trip in get_public_trips()
                if trip.get("owner_username") != current_user.id
            ]
            return no_update, _build_load_trip_items(trips, allow_delete=False, show_owner=True), active_trip_data, no_update, trips

        raise PreventUpdate

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data"),
        Output(ids.MODE_STORE, "data", allow_duplicate=True),
        Output(ids.BROWSE_OVERLAY_STORE, "data", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.VISIT_ORDER_STORE, "data", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Input({"type": "load-trip-item", "index": ALL}, "n_clicks"),
        State(ids.BROWSE_SAVED_TRIPS_STORE, "data"),
        State(ids.BROWSE_SHARED_TRIPS_STORE, "data"),
        prevent_initial_call=True,
    )
    def load_selected_trip(n_clicks_list, saved_trips, shared_trips):
        if not ctx.triggered_id or not any(n_clicks_list):
            raise PreventUpdate
        trip_id = ctx.triggered_id["index"]
        shared_trip = next((t for t in (shared_trips or []) if t["id"] == trip_id), None)
        trip = shared_trip or next((t for t in (saved_trips or []) if t["id"] == trip_id), None)
        if not trip:
            raise PreventUpdate
        if shared_trip:
            destination_ids = trip.get("landmark_ids") or trip.get("visit_order") or []
            destination_ids = [lid for lid in destination_ids if lid != -1]
            visit_order = [lid for lid in (trip.get("visit_order") or destination_ids) if lid != -1]
            return (
                None,
                "explore",
                False,
                destination_ids,
                visit_order,
                _build_selected_object_items(destination_ids),
            )

        active_trip = {
            "trip_id": trip["id"],
            "visit_order": trip["visit_order"] or [],
            "route_legs": trip["route_legs"],
            "current_point_index": trip["current_point_index"],
            "visited_indices": trip["visited_indices"],
            "custom_start_location": trip["custom_start_location"],
            "custom_end_location": trip["custom_end_location"],
            "saved_user_location": trip["saved_user_location"],
            "is_public": trip["is_public"],
            "owner_username": trip.get("owner_username", current_user.id),
        }
        return active_trip, "trip", False, no_update, no_update, no_update

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.SHARE_TRIP_TOAST, "children"),
        Output(ids.SHARE_TRIP_TOAST, "header"),
        Output(ids.SHARE_TRIP_TOAST, "icon"),
        Output(ids.SHARE_TRIP_TOAST, "is_open"),
        Input(ids.SHARE_TRIP_BTN, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def share_trip(n_clicks, active_trip):
        if not n_clicks:
            raise PreventUpdate
        if not active_trip or not active_trip.get("trip_id"):
            return no_update, "Load a trip before sharing it.", "Trip not loaded", "warning", True
        if active_trip.get("is_public"):
            return no_update, "This trip is already shared.", "Already shared", "info", True

        trip_id = active_trip["trip_id"]
        username = current_user.id
        try:
            set_trip_public_status(username, trip_id, True)
        except Exception as e:
            return no_update, f"Could not share this trip: {e}", "Sharing failed", "danger", True

        return {**active_trip, "is_public": True}, "Trip shared successfully.", "Shared", "success", True

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

    def _build_trip_content(active_trip):
        """Returns (trip_markers, polylines) for a given active_trip dict."""
        stop_ids = active_trip["visit_order"]
        current_idx = _clamp_stop_index(active_trip)
        visited = set(active_trip["visited_indices"])
        custom_start = active_trip.get("custom_start_location")
        custom_end = active_trip.get("custom_end_location")

        result = fetch_route_steps(
            registry.get_landmarks(stop_ids),
            start_point=_location_tuple(custom_start),
            end_point=_location_tuple(custom_end),
        )
        active_leg_idx = _active_route_leg_index(active_trip)
        trip_complete = _trip_complete(active_trip)
        passed_coords = []
        current_coords = []
        remaining_coords = []
        all_coords = []
        for i, segment in enumerate(result.segments):
            all_coords.extend(segment)
            if trip_complete or (active_leg_idx is not None and i < active_leg_idx):
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

        next_action_idx = _next_action_stop_index(active_trip)
        display_num = 0
        for i, lid in enumerate(stop_ids):
            lm = registry.get_landmark(lid)
            if not lm:
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
                    position=[lm.lat, lm.lon],
                    icon=icon,
                    children=[
                        dl.Tooltip(lm.name),
                        dl.Popup(html.Div([
                            html.H5(lm.name),
                            html.H6(lm.location),
                            html.A("Learn more", href=lm.link, target="_blank",
                                   style={"display": "block", "textAlign": "center"}),
                            popup_extra,
                        ])),
                    ],
                )
            )
        return saved_location_markers + markers, polylines

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
        Output(ids.TRIP_STATUS_PANEL, "children"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.GEOLOCATION, "position"),
    )
    def render_trip_status(active_trip, position):
        if not active_trip:
            return html.Div("Load a trip to see your progress.", className="text-muted small")

        stop_ids = active_trip.get("visit_order") or []
        if not stop_ids:
            return html.Div("This trip has no destinations.", className="text-muted small")

        current_idx = _clamp_stop_index(active_trip)
        trip_complete = _trip_complete(active_trip)
        next_action_idx = _next_action_stop_index(active_trip)
        current_point = _trip_point_summary(stop_ids, current_idx)
        custom_start = active_trip.get("custom_start_location")
        show_current_point = not (custom_start and not active_trip.get("visited_indices"))
        if show_current_point:
            visited = set(active_trip.get("visited_indices") or [])
            next_idx = next((i for i in range(current_idx + 1, len(stop_ids)) if i not in visited), None)
        else:
            next_idx = next_action_idx
        next_point = _trip_point_summary(stop_ids, next_idx) if next_idx is not None else None
        route_legs = _get_route_legs(active_trip, position)

        distance_to_next = None
        active_leg_idx = _active_route_leg_index(active_trip)
        if active_leg_idx is not None:
            for leg in route_legs:
                if leg.get("from_index") == active_leg_idx:
                    distance_to_next = leg.get("distance_m", 0)
                    break

        start_offset = 1 if custom_start else 0
        last_stop_route_idx = start_offset + len(stop_ids) - 1
        progress_legs = [
            leg for leg in route_legs
            if leg.get("to_index", 0) <= last_stop_route_idx
        ]
        if trip_complete:
            passed_distance = sum(leg.get("distance_m", 0) for leg in progress_legs)
            remaining_distance = 0
        else:
            passed_distance = sum(
                leg.get("distance_m", 0)
                for leg in progress_legs
                if active_leg_idx is not None and leg.get("from_index", 0) < active_leg_idx
            )
            remaining_distance = sum(
                leg.get("distance_m", 0)
                for leg in progress_legs
                if active_leg_idx is not None and leg.get("from_index", 0) >= active_leg_idx
            )
        total_distance = passed_distance + remaining_distance
        progress_pct = round((passed_distance / total_distance) * 100) if total_distance else 0

        def point_block(label, point):
            if not point:
                return html.Div([
                    html.Div(label, className="text-muted small"),
                    html.Div("Trip complete", style={"fontWeight": "600"}),
                ])
            return html.Div([
                html.Div(label, className="text-muted small"),
                html.Div(point["name"], style={"fontWeight": "600", "lineHeight": "1.2"}),
                html.Div(point["location"], className="text-muted small") if point["location"] else None,
            ])

        point_sections = [point_block("Next", next_point)]
        if show_current_point:
            point_sections = [
                point_block("Current", current_point),
                html.Hr(style={"margin": "0.5rem 0"}),
                *point_sections,
            ]

        return html.Div(
            [
                html.H6("Trip progress", className="mb-2"),
                *point_sections,
                html.Div(
                    [
                        html.Div("Distance to next", className="text-muted small"),
                        html.Div(
                            _format_distance(distance_to_next) if next_point else "0 m",
                            style={"fontWeight": "600"},
                        ),
                    ],
                    className="mt-2",
                ),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div(
                    [
                        html.Div([
                            html.Div("Passed", className="text-muted small"),
                            html.Div(_format_distance(passed_distance), style={"fontWeight": "600"}),
                        ]),
                        html.Div([
                            html.Div("Remaining", className="text-muted small"),
                            html.Div(_format_distance(remaining_distance), style={"fontWeight": "600"}),
                        ], style={"textAlign": "right"}),
                    ],
                    style={"display": "flex", "justifyContent": "space-between", "gap": "0.75rem"},
                ),
                dbc.Progress(value=progress_pct, className="mt-2", style={"height": "0.5rem"}),
            ]
        )

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
        return _build_all_markers(destination_ids or []), [], [], [], hidden_stats

    @app.callback(
        Output(ids.LOADED_TRIP_MARKERS_LAYER, "children"),
        Output(ids.LOADED_TRIP_POLYLINE_LAYER, "children"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.MODE_STORE, "data"),
        prevent_initial_call=True,
    )
    def render_trip_markers(active_trip, mode):
        if mode != "trip" or not active_trip:
            return [], []
        trip_markers, polylines = _build_trip_content(active_trip)
        return trip_markers, polylines

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Input({"type": "visit-btn", "index": ALL}, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def handle_visit_btn(n_clicks_list, active_trip):
        if not ctx.triggered_id or not any(n for n in n_clicks_list if n):
            raise PreventUpdate
        if not active_trip:
            raise PreventUpdate
        clicked_index = ctx.triggered_id["index"]
        stop_ids = active_trip.get("visit_order") or []
        if clicked_index != _next_action_stop_index(active_trip):
            raise PreventUpdate
        if clicked_index >= len(stop_ids):
            raise PreventUpdate

        if active_trip.get("owner_username", current_user.id) == current_user.id:
            update_trip_progress(
                trip_id=active_trip["trip_id"],
                new_current_index=clicked_index,
                newly_visited_index=clicked_index,
            )
        visited = list(active_trip["visited_indices"])
        if clicked_index not in visited:
            visited.append(clicked_index)
        return {
            **active_trip,
            "current_point_index": clicked_index,
            "visited_indices": visited,
        }

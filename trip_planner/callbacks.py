from dash import Output, Input, State, ALL, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import ids
## registry will be passed as a parameter
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon, number_icon, location_dot_icon
from marker_config import Landmark
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import dash_leaflet as dl
from flask_login import login_user
from backend.auth import verify_user, create_user, User

def register_callbacks(app, registry):
    def _build_all_markers(destination_ids):
        destination_ids = destination_ids or []
        return [
            dl.Marker(
                position=[lm.lat, lm.lon],
                children=[
                    dl.Tooltip(lm.name),
                    dl.Popup(html.Div([
                        html.H5(lm.name),
                        html.H6(lm.location),
                        html.A("Learn more", href=lm.link, target='_blank',
                               style={"display": "block", "text-align": "center"})
                    ]))
                ],
                id={"type": "marker", "index": lm.id},
                icon=checkbox_icon if lm.id in destination_ids else pin_icon
            )
            for lm in registry.landmarks
        ]

    @app.callback(
        Output("trip-polyline", "children"),
        Output(ids.WARN_MODAL, "is_open"),
        Output(ids.SUCCESS_TOAST, "is_open"),
        Output("all-markers-layer", "children"),
        Output("tour-markers-layer", "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline"),
        Output(ids.SAVE_TRIP_BTN, "disabled"),
        Output(ids.SAVE_TRIP_BTN, "color"),
        Output(ids.SAVE_TRIP_BTN, "style"),
        Output(ids.VISIT_ORDER_STORE, "data"),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        Input("warn-modal-close", "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        State(ids.GEOLOCATION, "position"),
        prevent_initial_call=True
    )
    def optimize_tsp(n_clicks, close_clicks, destination_ids, start_point_id, end_point_id, btn_label, position):
        if ctx.triggered_id == "warn-modal-close":
            return no_update, False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        if btn_label == "Modify Route":
            raise PreventUpdate
        if not destination_ids or len(destination_ids) < 2:
            return no_update, True, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        landmarks = registry.get_landmarks(destination_ids)
        start_landmark = None
        end_landmark = None
        if start_point_id == "my_location":
            if position:
                start_landmark = Landmark(id=-1, name="My location", location="", lat=position["lat"], lon=position["lon"])
        elif start_point_id and start_point_id != "auto":
            start_landmark = registry.get_landmark(int(start_point_id))
        if end_point_id == "my_location":
            if position:
                end_landmark = Landmark(id=-1, name="My location", location="", lat=position["lat"], lon=position["lon"])
        elif end_point_id and end_point_id != "auto":
            end_landmark = registry.get_landmark(int(end_point_id))
        visit_order = solve_tsp(landmarks, start_point=start_landmark, end_point=end_landmark)
        road_segments = fetch_route_steps(visit_order)
        colormap = cm.get_cmap("viridis", len(road_segments))
        colors = [mcolors.to_hex(colormap(i)) for i in range(len(road_segments))]
        polylines = [
            html.Div(dl.Polyline(positions=segment, color=color, weight=5))
            for segment, color in zip(road_segments, colors)
        ]
        start_is_my_location = start_landmark is not None and start_landmark.id == -1
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
                        html.A("Learn more", href=lm.link, target='_blank',
                               style={"display": "block", "text-align": "center"})
                    ]))
                ],
                icon=number_icon(visit_num[lm.id]),
            )
            for lm in visit_order
            if lm.id in visit_num
        ]
        visit_order_ids = [lm.id for lm in visit_order]
        return polylines, False, True, [], tour_markers, "Modify Route", "success", True, False, "info", {"flex": "1"}, visit_order_ids

    @app.callback(
        Output("trip-polyline", "children", allow_duplicate=True),
        Output("all-markers-layer", "children", allow_duplicate=True),
        Output("tour-markers-layer", "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        prevent_initial_call=True
    )
    def modify_route(n_clicks, destination_ids, btn_label):
        if btn_label != "Modify Route":
            raise PreventUpdate
        return [], _build_all_markers(destination_ids), [], "Optimize Route", "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}

    @app.callback(
        Output({"type": "marker", "index": ALL}, "icon"),
        Output(ids.SELECTED_OBJECTS_GROUP, "children"),
        Output(ids.DESTINATIONS_LIST, "data"),
        Input({"type": "marker", "index": ALL}, "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.SELECTED_OBJECTS_GROUP, "children"),
        prevent_initial_call=True
    )
    def toggle_marker(n_clicks_list, selected, current_children):
        if not ctx.triggered_id or not any(n_clicks_list):
            raise PreventUpdate
        if selected is None:
            selected = []
        if current_children is None:
            current_children = []
        landmark_id = ctx.triggered_id["index"]
        landmark = registry.get_landmark(landmark_id)
        if landmark_id in selected:
            selected.remove(landmark_id)
            current_children = [
                child for child in current_children
                if child["props"]["id"] != f"selected-item-{landmark_id}"
            ]
            icon = pin_icon
        else:
            selected.append(landmark_id)
            item = dbc.ListGroupItem([
                html.H6(landmark.name, className="mb-1 small"),
                html.P(landmark.location, className="mb-1 small"),
            ], className="p-3", id=f"selected-item-{landmark_id}")
            current_children.append(item)
            icon = checkbox_icon
        icons = []
        for l in ctx.inputs_list[0]:
            idx = l["id"]["index"]
            if idx == landmark_id:
                icons.append(icon)
            else:
                icons.append(checkbox_icon if idx in selected else pin_icon)
        return icons, current_children, selected

    @app.callback(
        Output("all-markers-layer", "children", allow_duplicate=True),
        Output("tour-markers-layer", "children", allow_duplicate=True),
        Output("trip-polyline", "children", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "outline", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "disabled", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "color", allow_duplicate=True),
        Output(ids.SAVE_TRIP_BTN, "style", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        prevent_initial_call=True
    )
    def clear_all(n_clicks):
        return _build_all_markers([]), [], [], [], [], "Optimize Route", "success", False, True, "secondary", {"opacity": "0.45", "flex": "1"}

    @app.callback(
        Output(ids.START_POINT_DROPDOWN, "options"),
        Output(ids.END_POINT_DROPDOWN, "options"),
        Output(ids.START_POINT_DROPDOWN, "value"),
        Output(ids.END_POINT_DROPDOWN, "value"),
        Input(ids.DESTINATIONS_LIST, "data"),
        Input(ids.GEOLOCATION, "position"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        prevent_initial_call=True
    )
    def update_dropdown_options(destination_ids, position, start_point_id, end_point_id):
        landmarks = registry.get_landmarks(destination_ids or [])
        auto_option = {"label": "Автоматично", "value": "auto"}
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
        prevent_initial_call=True,
    )
    def confirm_save_trip(n_clicks, name, landmark_ids, visit_order, start_value, end_value):
        from flask_login import current_user
        from backend.crud import save_trip
        if not name or not name.strip():
            return True, "Please enter a trip name.", True
        try:
            save_trip(
                username=current_user.id,
                name=name.strip(),
                landmark_ids=landmark_ids or [],
                visit_order=visit_order or [],
                used_user_location_start=(start_value == "my_location"),
                used_user_location_end=(end_value == "my_location"),
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
        accuracy = position.get("accuracy", 0)
        return [
            # Accuracy circle (vector layer — stays behind landmark markers)
            dl.Circle(
                center=[lat, lon],
                radius=accuracy,
                color="#1a6fcf",
                fillColor="#1a6fcf",
                fillOpacity=0.15,
                weight=1,
            ),
            # Location dot — Marker renders in the markerPane (above all vector layers)
            dl.Marker(
                position=[lat, lon],
                icon=location_dot_icon(),
                zIndexOffset=1000,
                children=dl.Tooltip("Your location"),
            ),
        ]

    # ─── Load Trip ───────────────────────────────────────────────
    @app.callback(
        Output(ids.LOAD_TRIP_MODAL, "is_open"),
        Output(ids.LOAD_TRIP_LIST, "children"),
        Input(ids.LOAD_TRIP_BTN, "n_clicks"),
        prevent_initial_call=True,
    )
    def open_load_trip_modal(n_clicks):
        from flask_login import current_user
        from backend.crud import get_user_trips
        trips = get_user_trips(current_user.id)
        if not trips:
            items = [dbc.ListGroupItem("No saved trips yet.", disabled=True)]
        else:
            items = [
                dbc.ListGroupItem(
                    [
                        html.Div(t["name"], style={"fontWeight": "600"}),
                        html.Small(t["created_at"], className="text-muted"),
                    ],
                    id={"type": "load-trip-item", "index": t["id"]},
                    action=True,
                    style={"cursor": "pointer"},
                )
                for t in trips
            ]
        return True, items

    @app.callback(
        Output(ids.LOAD_TRIP_MODAL, "is_open", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output("all-markers-layer", "children", allow_duplicate=True),
        Input({"type": "load-trip-item", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def load_selected_trip(n_clicks_list):
        if not ctx.triggered_id or not any(n_clicks_list):
            raise PreventUpdate
        trip_id = ctx.triggered_id["index"]
        from flask_login import current_user
        from backend.crud import get_user_trips
        trips = get_user_trips(current_user.id)
        trip = next((t for t in trips if t["id"] == trip_id), None)
        if not trip:
            raise PreventUpdate
        landmark_ids = trip["landmark_ids"]
        selected_items = []
        for lid in landmark_ids:
            lm = registry.get_landmark(lid)
            if lm:
                selected_items.append(
                    dbc.ListGroupItem([
                        html.H6(lm.name, className="mb-1 small"),
                        html.P(lm.location, className="mb-1 small"),
                    ], className="p-3", id=f"selected-item-{lid}")
                )
        markers = _build_all_markers(landmark_ids)
        return False, landmark_ids, selected_items, markers

from dash import Output, Input, State, ALL, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import ids
## registry will be passed as a parameter
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon, number_icon, location_dot_icon
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import dash_leaflet as dl
from flask_login import login_user
from auth import verify_user, create_user, User

def register_callbacks(app, registry):
    @app.callback(
        Output("trip-polyline", "children"),
        Output(ids.WARN_MODAL, "is_open"),
        Output(ids.SUCCESS_TOAST, "is_open"),
        Output({"type": "marker", "index": ALL}, "icon", allow_duplicate=True),
        Output({"type": "marker", "index": ALL}, "opacity", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children"),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color"),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        Input("warn-modal-close", "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        State({"type": "marker", "index": ALL}, "id"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        prevent_initial_call=True
    )
    def optimize_tsp(n_clicks, close_clicks, destination_ids, start_point_id, end_point_id, marker_ids, btn_label):
        if ctx.triggered_id == "warn-modal-close":
            return no_update, False, no_update, [no_update] * len(marker_ids), [no_update] * len(marker_ids), no_update, no_update
        if btn_label == "Modify Route":
            raise PreventUpdate
        if not destination_ids or len(destination_ids) < 2:
            return no_update, True, no_update, [no_update] * len(marker_ids), [no_update] * len(marker_ids), no_update, no_update
        landmarks = registry.get_landmarks(destination_ids)
        start_landmark = None
        end_landmark = None
        if start_point_id and start_point_id != "auto":
            start_landmark = registry.get_landmark(int(start_point_id))
        if end_point_id and end_point_id != "auto":
            end_landmark = registry.get_landmark(int(end_point_id))
        visit_order = solve_tsp(landmarks, start_point=start_landmark, end_point=end_landmark)
        road_segments = fetch_route_steps(visit_order)
        colormap = cm.get_cmap("viridis", len(road_segments))
        colors = [mcolors.to_hex(colormap(i)) for i in range(len(road_segments))]
        polylines = [
            html.Div(dl.Polyline(positions=segment, color=color, weight=5))
            for segment, color in zip(road_segments, colors)
        ]
        visit_num = {}
        for i, lm in enumerate(visit_order):
            if lm.id not in visit_num:
                visit_num[lm.id] = i + 1
        icons = [
            number_icon(visit_num[m["index"]]) if m["index"] in visit_num
            else (checkbox_icon if m["index"] in destination_ids else pin_icon)
            for m in marker_ids
        ]
        opacities = [1 if m["index"] in destination_ids else 0 for m in marker_ids]
        return polylines, False, True, icons, opacities, "Modify Route", "success"

    @app.callback(
        Output("trip-polyline", "children", allow_duplicate=True),
        Output({"type": "marker", "index": ALL}, "icon", allow_duplicate=True),
        Output({"type": "marker", "index": ALL}, "opacity", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        State({"type": "marker", "index": ALL}, "id"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.OPTIMIZE_ROUTE_BTN, "children"),
        prevent_initial_call=True
    )
    def modify_route(n_clicks, marker_ids, destination_ids, btn_label):
        if btn_label != "Modify Route":
            raise PreventUpdate
        icons = [checkbox_icon if m["index"] in (destination_ids or []) else pin_icon for m in marker_ids]
        opacities = [1 for _ in marker_ids]
        return [], icons, opacities, "Optimize Route", "primary"

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
        Output({"type": "marker", "index": ALL}, "icon", allow_duplicate=True),
        Output({"type": "marker", "index": ALL}, "opacity", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "children", allow_duplicate=True),
        Output(ids.OPTIMIZE_ROUTE_BTN, "color", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        State({"type": "marker", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    def clear_all(n_clicks, marker_ids):
        icons = [pin_icon for _ in marker_ids]
        opacities = [1 for _ in marker_ids]
        return icons, opacities, [], [], "Optimize Route", "primary"

    @app.callback(
        Output(ids.START_POINT_DROPDOWN, "options"),
        Output(ids.END_POINT_DROPDOWN, "options"),
        Output(ids.START_POINT_DROPDOWN, "value"),
        Output(ids.END_POINT_DROPDOWN, "value"),
        Input(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        prevent_initial_call=True
    )
    def update_dropdown_options(destination_ids, start_point_id, end_point_id):
        landmarks = registry.get_landmarks(destination_ids)
        auto_option = {"label": "Автоматично", "value": "auto"}
        options = [auto_option] + [{"label": l.name, "value": str(l.id)} for l in landmarks]
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
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "is_open", allow_duplicate=True),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, username, password):
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        if create_user(username, password):
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

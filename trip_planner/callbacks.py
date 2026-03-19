from dash import Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
from dash import html
import ids
## registry will be passed as a parameter
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import dash_leaflet as dl

def register_callbacks(app, registry):
    @app.callback(
        Output("trip-polyline", "children"),
        Output(ids.WARN_MODAL, "is_open"),
        Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
        Input("warn-modal-close", "n_clicks"),
        State(ids.DESTINATIONS_LIST, "data"),
        State(ids.START_POINT_DROPDOWN, "value"),
        State(ids.END_POINT_DROPDOWN, "value"),
        prevent_initial_call=True
    )
    def optimize_tsp(n_clicks, close_clicks, destination_ids, start_point_id, end_point_id):
        from dash import no_update
        if ctx.triggered_id == "warn-modal-close":
            return no_update, False
        if not destination_ids or len(destination_ids) < 2:
            return no_update, True
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
        return polylines, False

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
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Input(ids.CLEAR_ALL_BTN, "n_clicks"),
        State({"type": "marker", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    def clear_all(n_clicks, marker_ids):
        icons = [pin_icon for _ in marker_ids]
        return icons, [], []

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

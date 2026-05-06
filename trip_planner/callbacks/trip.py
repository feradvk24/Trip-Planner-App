from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user

import ids
from backend.crud import update_trip_progress
from callbacks.utils.routing import format_distance, get_route_legs
from callbacks.utils.trip_state import (
    active_route_leg_index,
    clamp_stop_index,
    next_action_stop_index,
    trip_complete,
    trip_point_summary,
    visit_stop,
)
from callbacks.widgets.review_widgets import review_pane_state, trip_completion_review_pane_state
from callbacks.widgets.trip_rendering import build_trip_content


def register_trip_callbacks(app, registry):
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

        current_idx = clamp_stop_index(active_trip)
        is_trip_complete = trip_complete(active_trip)
        next_action_idx = next_action_stop_index(active_trip)
        current_point = trip_point_summary(registry, stop_ids, current_idx, active_trip)
        custom_start = active_trip.get("custom_start_location")
        show_current_point = not (custom_start and not active_trip.get("visited_indices"))
        if show_current_point:
            visited = set(active_trip.get("visited_indices") or [])
            next_idx = next((i for i in range(current_idx + 1, len(stop_ids)) if i not in visited), None)
            if next_idx is None:
                next_idx = next_action_idx
        else:
            next_idx = next_action_idx
        next_point = trip_point_summary(registry, stop_ids, next_idx, active_trip) if next_idx is not None else None
        route_legs = get_route_legs(registry, active_trip)

        distance_to_next = None
        active_leg_idx = active_route_leg_index(active_trip)
        if active_leg_idx is not None:
            for leg in route_legs:
                if leg.get("from_index") == active_leg_idx:
                    distance_to_next = leg.get("distance_m", 0)
                    break

        start_offset = 1 if custom_start else 0
        last_stop_route_idx = start_offset + len(stop_ids) - 1 + int(bool(active_trip.get("custom_end_location")))
        progress_legs = [
            leg for leg in route_legs
            if leg.get("to_index", 0) <= last_stop_route_idx
        ]
        if is_trip_complete:
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
                dbc.Button(
                    "Visit",
                    id=ids.TRIP_NEXT_VISIT_BTN,
                    color="success",
                    size="sm",
                    className="mt-2 w-100",
                ) if next_action_idx is not None and next_point else None,
                html.Div(
                    [
                        html.Div("Distance to next", className="text-muted small"),
                        html.Div(
                            format_distance(distance_to_next) if next_point else "0 m",
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
                            html.Div(format_distance(passed_distance), style={"fontWeight": "600"}),
                        ]),
                        html.Div([
                            html.Div("Remaining", className="text-muted small"),
                            html.Div(format_distance(remaining_distance), style={"fontWeight": "600"}),
                        ], style={"textAlign": "right"}),
                    ],
                    style={"display": "flex", "justifyContent": "space-between", "gap": "0.75rem"},
                ),
                dbc.Progress(value=progress_pct, className="mt-2", style={"height": "0.5rem"}),
            ]
        )

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
        trip_markers, polylines = build_trip_content(registry, active_trip)
        return trip_markers, polylines

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.LANDMARK_REVIEW_STATE_STORE, "data"),
        Output(ids.LANDMARK_REVIEW_TEXT, "value"),
        Output(ids.LANDMARK_REVIEW_ALERT, "is_open"),
        Input({"type": "visit-btn", "index": ALL}, "n_clicks"),
        Input(ids.TRIP_NEXT_VISIT_BTN, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def handle_visit_btn(n_clicks_list, progress_clicks, active_trip):
        if not ctx.triggered_id:
            raise PreventUpdate
        if ctx.triggered_id == ids.TRIP_NEXT_VISIT_BTN:
            if not progress_clicks:
                raise PreventUpdate
            clicked_index = next_action_stop_index(active_trip)
        else:
            if not any(n for n in n_clicks_list if n):
                raise PreventUpdate
            clicked_index = ctx.triggered_id["index"]

        updated_trip = visit_stop(active_trip, clicked_index, current_user.id, update_trip_progress)
        completion_review_state = (
            trip_completion_review_pane_state(updated_trip)
            if trip_complete(updated_trip)
            else None
        )

        try:
            review_state = review_pane_state(registry, active_trip, clicked_index)
        except PreventUpdate:
            if not completion_review_state:
                raise
            return updated_trip, completion_review_state, "", False

        if completion_review_state:
            review_state["next_review_state"] = completion_review_state
        return updated_trip, review_state, "", False

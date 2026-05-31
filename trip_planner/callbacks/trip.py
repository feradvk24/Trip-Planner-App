from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user

import ids
from services.landmark_registry import LandmarkRegistry
from services.trip_route import TripRoute
from services.trip_workflows import visit_trip_stop_for_user
from callbacks.utils.get_language import get_language_from_url
from callbacks.utils.routing import format_distance, get_route_legs
from callbacks.utils.trip_state import trip_point_summary
from callbacks.widgets.review_widgets import review_pane_state, trip_completion_review_pane_state
from callbacks.widgets.trip_rendering import build_trip_content
from i18n import t


def hidden_next_visit_button(lang="bg"):
    return dbc.Button(
        t("sidebar.visit", lang=lang),
        id=ids.TRIP_NEXT_VISIT_BTN,
        disabled=True,
        style={"display": "none"},
    )


def register_trip_callbacks(app):
    registry = LandmarkRegistry.get_landmarks()

    @app.callback(
        Output(ids.TRIP_STATUS_PANEL, "children"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.GEOLOCATION, "position"),
        State("url", "href"),
    )
    def render_trip_status(active_trip, position, href):
        lang = get_language_from_url(href)
        if not active_trip:
            return html.Div([
                html.Div(t("trip_status.load_trip_progress", lang=lang), className="text-muted small"),
                hidden_next_visit_button(lang=lang),
            ])

        visit_order = active_trip.get("visit_order") or []
        if not visit_order:
            return html.Div([
                html.Div(t("trip_status.no_destinations", lang=lang), className="text-muted small"),
                hidden_next_visit_button(lang=lang),
            ])

        show_current_point = bool(active_trip.get("visited_indices"))
        route_legs = get_route_legs(registry, active_trip)
        active_trip = {**active_trip, "route_legs": list(route_legs or [])}
        trip_route = TripRoute.from_store(active_trip)
        stop_count = trip_route.action_stop_count
        current_idx = max(0, min(active_trip.get("current_point_index", 0), stop_count - 1)) if stop_count else 0
        current_point = trip_point_summary(registry, visit_order, current_idx, active_trip, lang=lang)
        next_action_idx = trip_route.next_action_index()
        if show_current_point:
            visited = trip_route.visited_indices
            next_idx = next((i for i in range(current_idx + 1, len(visit_order)) if i not in visited), None)
            if next_idx is None:
                next_idx = next_action_idx
        else:
            next_idx = next_action_idx
        next_point = trip_point_summary(registry, visit_order, next_idx, active_trip, lang=lang) if next_idx is not None else None
        progress = trip_route.progress_summary()

        def point_block(label, point):
            if not point:
                return html.Div([
                    html.Div(label, className="text-muted small"),
                    html.Div(t("trip_status.trip_complete", lang=lang), style={"fontWeight": "600"}),
                ])
            return html.Div([
                html.Div(label, className="text-muted small"),
                html.Div(point["name"], style={"fontWeight": "600", "lineHeight": "1.2"}),
                html.Div(point["location"], className="text-muted small") if point["location"] else None,
            ])

        point_sections = [point_block(t("trip_status.next", lang=lang), next_point)]
        if show_current_point:
            point_sections = [
                point_block(t("trip_status.current", lang=lang), current_point),
                html.Hr(style={"margin": "0.5rem 0"}),
                *point_sections,
            ]

        return html.Div(
            [
                html.H6(t("trip_status.trip_progress", lang=lang), className="mb-2"),
                *point_sections,
                dbc.Button(
                    t("sidebar.visit", lang=lang),
                    id=ids.TRIP_NEXT_VISIT_BTN,
                    color="success",
                    size="sm",
                    className="mt-2 w-100",
                ) if next_action_idx is not None and next_point else hidden_next_visit_button(lang=lang),
                html.Div(
                    [
                        html.Div(t("trip_status.distance_to_next", lang=lang), className="text-muted small"),
                        html.Div(
                            format_distance(progress["distance_to_next_m"]) if next_point else "0 m",
                            style={"fontWeight": "600"},
                        ),
                    ],
                    className="mt-2",
                ),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div(
                    [
                        html.Div([
                            html.Div(t("trip_status.passed", lang=lang), className="text-muted small"),
                            html.Div(format_distance(progress["passed_distance_m"]), style={"fontWeight": "600"}),
                        ]),
                        html.Div([
                            html.Div(t("trip_status.remaining", lang=lang), className="text-muted small"),
                            html.Div(format_distance(progress["remaining_distance_m"]), style={"fontWeight": "600"}),
                        ], style={"textAlign": "right"}),
                    ],
                    style={"display": "flex", "justifyContent": "space-between", "gap": "0.75rem"},
                ),
                dbc.Progress(value=progress["progress_percent"], className="mt-2", style={"height": "0.5rem"}),
            ]
        )

    @app.callback(
        Output(ids.LOADED_TRIP_MARKERS_LAYER, "children"),
        Output(ids.LOADED_TRIP_POLYLINE_LAYER, "children"),
        Output(ids.LOADED_TRIP_OVERVIEW_POLYLINE_LAYER, "children"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.MODE_STORE, "data"),
        State("url", "href"),
    )
    def render_trip_markers(active_trip, mode, href):
        if mode != "trip" or not active_trip:
            return [], [], []
        lang = get_language_from_url(href)
        trip_markers, status_polylines, overview_polylines = build_trip_content(registry, active_trip, lang=lang)
        return trip_markers, status_polylines, overview_polylines

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
        active_route = TripRoute.from_store(active_trip)
        if ctx.triggered_id == ids.TRIP_NEXT_VISIT_BTN:
            if not progress_clicks:
                raise PreventUpdate
            clicked_index = active_route.next_action_index()
        else:
            if not any(n for n in n_clicks_list if n):
                raise PreventUpdate
            clicked_index = ctx.triggered_id["index"]

        try:
            result = visit_trip_stop_for_user(current_user.id, active_trip, clicked_index, route=active_route)
        except ValueError:
            raise PreventUpdate

        updated_trip = result.data["updated_trip"]
        completion_review_state = (
            trip_completion_review_pane_state(updated_trip)
            if result.data["is_now_complete"]
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

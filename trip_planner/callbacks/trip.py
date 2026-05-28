from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_login import current_user

import ids
from backend.crud import create_trip_completion, update_trip_progress
from services.landmark_registry import LandmarkRegistry
from callbacks.utils import trip_state
from callbacks.utils.get_language import get_language_from_url
from callbacks.utils.routing import format_distance, get_route_legs
from callbacks.utils.trip_state import trip_point_summary, visit_stop
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


def _trip_progress_summary(active_trip):
    route_legs = active_trip.get("route_legs") or []
    visit_order = active_trip.get("visit_order") or []
    custom_start = active_trip.get("custom_start_location")
    custom_end = active_trip.get("custom_end_location")
    start_offset = int(bool(custom_start))
    last_route_index = (
        int(bool(custom_end))
        if not visit_order else
        start_offset + len(visit_order) - 1 + int(bool(custom_end))
    )
    progress_legs = [
        leg for leg in route_legs
        if leg.get("to_index", 0) <= last_route_index
    ]

    active_index = trip_state.active_leg_index(active_trip)
    distance_to_next = None
    if active_index is not None:
        for fallback_index, leg in enumerate(route_legs):
            if leg.get("from_index") == active_index or fallback_index == active_index:
                distance_to_next = leg.get("distance_m", 0)
                break

    if trip_state.is_complete(active_trip):
        passed = sum(leg.get("distance_m", 0) for leg in progress_legs)
        remaining = 0
    else:
        passed = sum(
            leg.get("distance_m", 0)
            for leg in progress_legs
            if active_index is not None and leg.get("from_index", 0) < active_index
        )
        remaining = sum(
            leg.get("distance_m", 0)
            for leg in progress_legs
            if active_index is None or leg.get("from_index", 0) >= active_index
        )

    total = passed + remaining
    return {
        "distance_to_next_m": distance_to_next,
        "passed_distance_m": passed,
        "remaining_distance_m": remaining,
        "progress_percent": round((passed / total) * 100) if total else 0,
    }


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
        stop_count = len(visit_order) + int(bool(active_trip.get("custom_end_location")))
        current_idx = max(0, min(active_trip.get("current_point_index", 0), stop_count - 1)) if stop_count else 0
        current_point = trip_point_summary(registry, visit_order, current_idx, active_trip, lang=lang)
        is_trip_complete = trip_state.is_complete(active_trip)
        next_action_idx = trip_state.next_action_index(active_trip)
        if show_current_point:
            visited = trip_state.visited_set(active_trip)
            next_idx = next((i for i in range(current_idx + 1, len(visit_order)) if i not in visited), None)
            if next_idx is None:
                next_idx = next_action_idx
        else:
            next_idx = next_action_idx
        next_point = trip_point_summary(registry, visit_order, next_idx, active_trip, lang=lang) if next_idx is not None else None
        progress = _trip_progress_summary(active_trip)

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
        if ctx.triggered_id == ids.TRIP_NEXT_VISIT_BTN:
            if not progress_clicks:
                raise PreventUpdate
            clicked_index = trip_state.next_action_index(active_trip)
        else:
            if not any(n for n in n_clicks_list if n):
                raise PreventUpdate
            clicked_index = ctx.triggered_id["index"]

        updated_trip = visit_stop(active_trip, clicked_index, update_trip_progress)
        trip_was_completed = trip_state.is_complete(updated_trip)
        completion_review_state = trip_completion_review_pane_state(updated_trip) if trip_was_completed else None
        if trip_was_completed and not trip_state.is_complete(active_trip):
            create_trip_completion(
                username=current_user.id,
                trip_id=updated_trip["trip_id"],
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

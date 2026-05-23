import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate
from flask_login import current_user

import ids
from backend.crud import (
    delete_trip,
    get_public_trips,
    get_user_landmark_visit_history,
    get_user_trips,
    set_active_user_trip,
    set_trip_public_status,
)
from callbacks.utils.trip_state import sanitize_shared_trip
from callbacks.widgets.callback_widgets import build_load_trip_items, build_selected_object_items


MAX_VISIT_HISTORY_ITEMS = 100


def build_visit_history_items(registry, visits, limit=MAX_VISIT_HISTORY_ITEMS):
    visits = (visits or [])[:limit]
    if not visits:
        return [
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.Div("No visited landmarks yet.", className="fw-semibold"),
                        html.Div(
                            "Visited landmarks will appear here after you progress through a trip.",
                            className="text-muted small",
                        ),
                    ],
                    className="py-2",
                )
            )
        ]

    items = []
    for visit in visits:
        landmark = registry.get_landmark(visit.get("landmark_id"))
        landmark_name = landmark.name if landmark else f"Landmark {visit.get('landmark_id')}"
        landmark_location = landmark.location if landmark else ""
        items.append(
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(landmark_name, className="fw-semibold"),
                                html.Small(visit.get("visited_at", ""), className="text-muted"),
                            ],
                            className="d-flex justify-content-between gap-3",
                        ),
                        html.Div(landmark_location, className="text-muted small"),
                        html.Div(
                            f"Trip: {visit.get('trip_name', 'Unknown trip')}",
                            className="small",
                        ),
                    ],
                    className="d-flex flex-column gap-1",
                )
            )
        )
    return items


def register_browse_callbacks(app, registry):
    @app.callback(
        Output(ids.LOAD_TRIP_LIST, "children"),
        Output(ids.USER_SHARED_TRIPS_LIST, "children"),
        Output(ids.VISIT_HISTORY_LIST, "children"),
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.BROWSE_SAVED_TRIPS_STORE, "data"),
        Output(ids.BROWSE_SHARED_TRIPS_STORE, "data"),
        Output(ids.BROWSE_VISIT_HISTORY_STORE, "data"),
        Output(ids.SELECTED_TRIP_STORE, "data", allow_duplicate=True),
        Input("url", "pathname"),
        Input(ids.BROWSE_OVERLAY_STORE, "data"),
        Input(ids.BROWSE_TABS, "active_tab"),
        Input({"type": "delete-trip-item", "index": ALL}, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        State(ids.SELECTED_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def refresh_browse_saved_trips(pathname, browse_open, active_tab, delete_clicks_list, active_trip, selected_trip):
        on_browse_page = pathname == "/browse"
        active_tab = active_tab or "my-saved-trips"
        active_trip_data = no_update
        selected_trip_data = no_update
        if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "delete-trip-item":
            trip_id = ctx.triggered_id["index"]
            delete_trip(current_user.id, trip_id)
            if active_trip and active_trip.get("trip_id") == trip_id:
                active_trip_data = None
            if selected_trip and selected_trip.get("id") == trip_id:
                selected_trip_data = None
            trips = get_user_trips(current_user.id, include_completion_status=True)
            return build_load_trip_items(trips), no_update, no_update, active_trip_data, trips, no_update, no_update, selected_trip_data

        if not browse_open and not on_browse_page:
            raise PreventUpdate
        if ctx.triggered_id in ("url", ids.BROWSE_OVERLAY_STORE, ids.BROWSE_TABS):
            selected_trip_data = None

        if active_tab == "my-saved-trips":
            trips = get_user_trips(current_user.id, include_completion_status=True)
            return build_load_trip_items(trips), no_update, no_update, active_trip_data, trips, no_update, no_update, selected_trip_data

        if active_tab == "user-shared-trips":
            trips = [
                sanitize_shared_trip(trip) for trip in get_public_trips(include_completion_status=True)
                if trip.get("owner_username") != current_user.id
            ]
            return no_update, build_load_trip_items(trips, allow_delete=False, show_owner=True), no_update, active_trip_data, no_update, trips, no_update, selected_trip_data

        if active_tab == "visit-history":
            visits = get_user_landmark_visit_history(current_user.id, limit=MAX_VISIT_HISTORY_ITEMS)
            return no_update, no_update, build_visit_history_items(registry, visits), active_trip_data, no_update, no_update, visits, selected_trip_data

        raise PreventUpdate

    @app.callback(
        Output(ids.SELECTED_TRIP_STORE, "data"),
        Input({"type": "load-trip-item", "index": ALL}, "n_clicks"),
        State(ids.BROWSE_SAVED_TRIPS_STORE, "data"),
        State(ids.BROWSE_SHARED_TRIPS_STORE, "data"),
        prevent_initial_call=True,
    )
    def preview_selected_trip(n_clicks_list, saved_trips, shared_trips):
        triggered_value = ctx.triggered[0].get("value") if ctx.triggered else None
        if not ctx.triggered_id or not triggered_value:
            raise PreventUpdate
        trip_id = ctx.triggered_id["index"]
        shared_trip = next((t for t in (shared_trips or []) if t["id"] == trip_id), None)
        trip = shared_trip or next((t for t in (saved_trips or []) if t["id"] == trip_id), None)
        if not trip:
            raise PreventUpdate
        return {
            **trip,
            "source": "shared" if shared_trip else "saved",
        }

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data"),
        Output(ids.MODE_STORE, "data", allow_duplicate=True),
        Output(ids.BROWSE_OVERLAY_STORE, "data", allow_duplicate=True),
        Output(ids.DESTINATIONS_LIST, "data", allow_duplicate=True),
        Output(ids.VISIT_ORDER_STORE, "data", allow_duplicate=True),
        Output(ids.SELECTED_OBJECTS_GROUP, "children", allow_duplicate=True),
        Output("url", "href", allow_duplicate=True),
        Input(ids.SELECT_TRIP_BTN, "n_clicks"),
        State(ids.SELECTED_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def load_selected_trip(n_clicks, trip):
        if not n_clicks or not trip:
            raise PreventUpdate
        shared_trip = trip.get("source") == "shared"
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
                build_selected_object_items(registry, destination_ids),
                "/",
            )

        active_trip = set_active_user_trip(current_user.id, trip["id"])
        return active_trip, "trip", False, no_update, no_update, no_update, "/"

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

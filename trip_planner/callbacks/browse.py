from dash import ALL, Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
from flask import session
from flask_login import current_user

import ids
from backend.crud import (
    clear_active_user_trip,
    delete_trip,
    get_public_trips,
    get_user_trips,
    set_active_user_trip,
    set_trip_public_status,
)
from callbacks.utils.trip_state import sanitize_shared_trip
from callbacks.utils.get_language import get_language_from_url
from callbacks.widgets.callback_widgets import build_load_trip_items
from i18n import t


def is_browse_path(pathname):
    return (pathname or "").rstrip("/").endswith("/browse")

def register_browse_callbacks(app):
    @app.callback(
        Output(ids.LOAD_TRIP_LIST, "children"),
        Output(ids.USER_SHARED_TRIPS_LIST, "children"),
        Output(ids.BROWSE_SAVED_TRIPS_STORE, "data"),
        Output(ids.BROWSE_SHARED_TRIPS_STORE, "data"),
        Output(ids.SELECTED_TRIP_STORE, "data", allow_duplicate=True),
        Input(ids.BROWSE_TABS, "active_tab", allow_optional=True),
        Input({"type": "delete-trip-item", "index": ALL}, "n_clicks"),
        State("url", "pathname"),
        State(ids.SELECTED_TRIP_STORE, "data"),
        prevent_initial_call=True,
    )
    def refresh_browse_saved_trips(active_tab, delete_clicks_list, pathname, selected_trip):
        lang = get_language_from_url(pathname)
        on_browse_page = is_browse_path(pathname)
        active_tab = active_tab or "my-saved-trips"
        selected_trip_data = no_update
        if not on_browse_page:
            raise PreventUpdate

        if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "delete-trip-item":
            trip_id = ctx.triggered_id["index"]
            delete_trip(current_user.id, trip_id)
            if selected_trip and selected_trip.get("id") == trip_id:
                selected_trip_data = None
            trips = get_user_trips(current_user.id, include_completion_status=True)
            return build_load_trip_items(trips, lang=lang), no_update, trips, no_update, selected_trip_data

        if ctx.triggered_id == ids.BROWSE_TABS:
            selected_trip_data = None

        if active_tab == "my-saved-trips":
            trips = get_user_trips(current_user.id, include_completion_status=True)
            return build_load_trip_items(trips, lang=lang), no_update, trips, no_update, selected_trip_data

        if active_tab == "user-shared-trips":
            trips = [
                sanitize_shared_trip(trip) for trip in get_public_trips(include_completion_status=True)
                if trip.get("owner_username") != current_user.id
            ]
            return no_update, build_load_trip_items(trips, allow_delete=False, show_owner=True, lang=lang), no_update, trips, selected_trip_data

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
        Output("url", "href", allow_duplicate=True),
        Input(ids.SELECT_TRIP_BTN, "n_clicks"),
        State(ids.SELECTED_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def load_selected_trip(n_clicks, trip, href):
        if not n_clicks or not trip:
            raise PreventUpdate
        lang = get_language_from_url(href)
        shared_trip = trip.get("source") == "shared"
        if shared_trip:
            clear_active_user_trip(current_user.id)
            session["pending_browse_trip"] = {
                "shared_trip_id": trip["id"],
            }
            return f"/{lang}"

        set_active_user_trip(current_user.id, trip["id"])
        return f"/{lang}"

    @app.callback(
        Output(ids.ACTIVE_TRIP_STORE, "data", allow_duplicate=True),
        Output(ids.SHARE_TRIP_TOAST, "children"),
        Output(ids.SHARE_TRIP_TOAST, "header"),
        Output(ids.SHARE_TRIP_TOAST, "icon"),
        Output(ids.SHARE_TRIP_TOAST, "is_open"),
        Input(ids.SHARE_TRIP_BTN, "n_clicks"),
        Input(ids.LANDMARK_REVIEW_SHARE_TRIP_BTN, "n_clicks"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def share_trip(sidebar_clicks, completion_clicks, active_trip, href):
        if not sidebar_clicks and not completion_clicks:
            raise PreventUpdate
        lang = get_language_from_url(href)
        if not active_trip or not active_trip.get("trip_id"):
            return no_update, t("share_trip.load_before_sharing", lang=lang), t("share_trip.not_loaded", lang=lang), "warning", True
        if active_trip.get("is_public"):
            return no_update, t("share_trip.already_shared_message", lang=lang), t("share_trip.already_shared", lang=lang), "info", True

        trip_id = active_trip["trip_id"]
        username = current_user.id
        try:
            set_trip_public_status(username, trip_id, True)
        except Exception as e:
            return no_update, f"{t('share_trip.failed_message', lang=lang)}: {e}", t("share_trip.failed", lang=lang), "danger", True

        return {**active_trip, "is_public": True}, t("share_trip.success_message", lang=lang), t("share_trip.shared", lang=lang), "success", True

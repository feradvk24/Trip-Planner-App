import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask import session
from flask_login import current_user

import ids
from backend.crud import get_active_user_trip
from callbacks.utils.trip_state import next_action_stop_index
from layout.info_sidebar import create_info_sidebar
from layout.map import create_map
from layout.overlays import create_browse_overlay, create_landmark_review_pane
from layout.sidebar import create_sidebar, create_user_menu
from styles import CONTENT_STYLE
from i18n import t

def initial_active_info(active_trip=None):
    if not active_trip:
        return None

    stop_ids = active_trip.get("visit_order") or []
    next_stop_index = next_action_stop_index(active_trip)
    if next_stop_index is None:
        return None

    if next_stop_index >= len(stop_ids):
        return None

    landmark_id = stop_ids[next_stop_index]
    if landmark_id == -1:
        return None

    return {
        "type": "trip",
        "content": landmark_id,
    }


def create_stores(active_trip=None, pending_browse_trip=None, focused_landmark_id=None):
    if pending_browse_trip:
        initial_mode = pending_browse_trip.get("mode") or "explore"
        initial_destinations = pending_browse_trip.get("destination_ids") or []
        initial_visit_order = pending_browse_trip.get("visit_order") or []
        initial_active_trip = pending_browse_trip.get("active_trip")
        initial_info = initial_active_info(initial_active_trip)
    elif focused_landmark_id:
        initial_mode = "explore"
        initial_destinations = []
        initial_visit_order = []
        initial_active_trip = None
        initial_info = {
            "type": "landmark",
            "content": focused_landmark_id,
        }
    else:
        initial_mode = "trip" if active_trip else "explore"
        initial_destinations = []
        initial_visit_order = []
        initial_active_trip = active_trip
        initial_info = initial_active_info(initial_active_trip)

    store_type = "memory" if focused_landmark_id else "session"

    return [
        dcc.Store(id=ids.DESTINATIONS_LIST, data=initial_destinations, storage_type=store_type),
        dcc.Store(id=ids.VISIT_ORDER_STORE, data=initial_visit_order, storage_type=store_type),
        dcc.Store(id=ids.MODE_STORE, data=initial_mode, storage_type=store_type),
        dcc.Store(id=ids.BROWSE_OVERLAY_STORE, data=False),
        dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.SELECTED_TRIP_STORE, data=None),
        dcc.Store(id=ids.ACTIVE_TRIP_STORE, data=initial_active_trip, storage_type=store_type),
        dcc.Store(id=ids.EXPLORE_MAP_CACHE, data=None, storage_type=store_type),
        dcc.Store(id=ids.ACTIVE_INFO_STORE, data=initial_info, storage_type=store_type),
        dcc.Store(id=ids.OPTIMIZED_TRIP_STORE, data=None, storage_type=store_type),
    ]


def create_save_trip_modal(lang="bg"):
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(t("save_trip_modal.title", lang=lang))),
        dbc.ModalBody([
            dbc.Alert(id=ids.SAVE_TRIP_ALERT, is_open=False, color="danger", duration=4000),
            dbc.Label(t("save_trip_modal.trip_name", lang=lang)),
            dbc.Input(id=ids.SAVE_TRIP_NAME_INPUT, placeholder=t("save_trip_modal.placeholder", lang=lang), maxLength=200),
        ]),
        dbc.ModalFooter([
            dbc.Button(t("save_trip_modal.save", lang=lang), id=ids.SAVE_TRIP_CONFIRM_BTN, color="info"),
            dbc.Button(t("save_trip_modal.cancel", lang=lang), id="save-trip-cancel-btn", color="secondary", outline=True, className="ms-2"),
        ]),
    ], id=ids.SAVE_TRIP_MODAL, is_open=False)


def create_warn_modal(lang="bg"):
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(t("warn_modal.title", lang=lang))),
        dbc.ModalBody(t("warn_modal.message", lang=lang)),
        dbc.ModalFooter(dbc.Button(t("warn_modal.ok", lang=lang), id="warn-modal-close", color="primary")),
    ], id=ids.WARN_MODAL, is_open=False)


def create_success_toast(lang="bg"):
    return dbc.Toast(
        t("success_toast.message", lang=lang),
        id=ids.SUCCESS_TOAST,
        header=t("success_toast.header", lang=lang),
        icon="success",
        is_open=False,
        dismissable=True,
        duration=2000,
        style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999, "minWidth": "auto"},
    )


def create_share_trip_toast(lang="bg"):
    return dbc.Toast(
        t("share_trip_toast.message", lang=lang),
        id=ids.SHARE_TRIP_TOAST,
        header=t("share_trip_toast.header", lang=lang),
        icon="info",
        is_open=False,
        dismissable=True,
        duration=3500,
        style={"position": "fixed", "bottom": "4.75rem", "right": "1rem", "zIndex": 9999, "minWidth": "18rem"},
    )


def create_main_content(markers, active_trip=None, focused_landmark=None, lang="bg"):
    initial_markers = [] if active_trip else markers
    initial_viewport = None
    if focused_landmark:
        initial_viewport = {
            "center": [focused_landmark.lat, focused_landmark.lon],
            "zoom": 14,
            "transition": "setView",
        }

    return html.Div(
        id=ids.MAIN_CONTENT,
        style=CONTENT_STYLE,
        children=[
            dbc.Container(fluid=True, className="h-100 d-flex flex-column p-0", children=[
                dbc.Row(className="h-100 flex-grow-1 p-0", children=[
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    create_map(initial_markers, initial_viewport),
                                    create_browse_overlay(lang=lang),
                                ],
                                className="flex-grow-1",
                                style={"minHeight": 0, "position": "relative"},
                            ),
                        ],
                        width=12,
                        className="d-flex flex-column",
                    )
                ])
            ])
        ],
    )


def create_authenticated_layout(markers, include_location=True, focused_landmark_id=None, lang="bg"):
    pending_browse_trip = session.pop("pending_browse_trip", None)
    focused_landmark = None
    if focused_landmark_id:
        try:
            import app_context

            focused_landmark = app_context.REGISTRY.get_landmark(int(focused_landmark_id))
        except (TypeError, ValueError, AttributeError):
            focused_landmark = None

    if focused_landmark:
        active_trip = None
    else:
        active_trip = get_active_user_trip(current_user.id)
    children = [
        dcc.Geolocation(id=ids.GEOLOCATION, high_accuracy=True, maximum_age=0, update_now=True, timeout=10000),
        create_sidebar(active_trip, lang=lang),
        create_info_sidebar(lang=lang),
        create_main_content(markers, active_trip, focused_landmark, lang=lang),
        create_landmark_review_pane(lang=lang),
        create_user_menu(lang=lang),
        *create_stores(active_trip, pending_browse_trip, focused_landmark.id if focused_landmark else None),
        create_warn_modal(lang=lang),
        create_success_toast(lang=lang),
        create_share_trip_toast(lang=lang),
        create_save_trip_modal(lang=lang),
    ]
    if include_location:
        children.insert(0, dcc.Location(id="url"))
    return html.Div(children)


def create_app_layout(markers):
    return html.Div([
        dcc.Location(id="url"),
        dash.page_container,
    ])

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask import session
from flask_login import current_user

import ids
from backend.auth import is_admin_panel_user
from backend.db.crud import get_active_user_trip, get_public_trip
from services.landmark_registry import LandmarkRegistry
from services.trip_route import TripRoute
from dash_store_schemas.stores import ActiveInfoStore, ActiveTripStore, PendingBrowseTripStore
from callbacks.utils.trip_state import sanitize_shared_trip
from layout.info_sidebar import create_info_sidebar
from layout.map import create_map
from layout.overlays import create_landmark_review_pane
from layout.sidebar import create_sidebar, create_user_menu
from styles import CONTENT_STYLE
from i18n import t

def initial_active_info(active_trip: ActiveTripStore | None = None) -> ActiveInfoStore | None:
    if not active_trip:
        return None

    store = TripRoute.handle_trip_store(active_trip)
    next_index = next(
        (index for index in range(len(store["visit_order"])) if index not in store["visited_set"]),
        None,
    )
    landmark_id = store["visit_order"][next_index] if next_index is not None else None
    if landmark_id is None:
        return None

    return {
        "type": "trip",
        "content": landmark_id,
    }


def resolve_pending_browse_trip(
    pending_browse_trip: PendingBrowseTripStore | None,
    registry=None,
) -> PendingBrowseTripStore | None:
    if not pending_browse_trip:
        return None

    shared_trip_id = pending_browse_trip.get("shared_trip_id")
    if not shared_trip_id:
        return pending_browse_trip

    shared_trip = get_public_trip(shared_trip_id)
    if not shared_trip:
        return None

    shared_trip = sanitize_shared_trip(shared_trip)
    shared_store = TripRoute.handle_trip_store(shared_trip)
    return {
        "active_trip": None,
        "mode": "explore",
        "destination_ids": shared_store["destination_ids"],
        "visit_order": shared_trip.get("visit_order") or shared_trip.get("landmark_ids") or [],
        "optimized_trip": {
            "visit_order": shared_store["visit_order"],
            "route_legs": shared_store["route_legs"],
            "custom_start_location": shared_store["custom_start_location"],
            "custom_end_location": shared_store["custom_end_location"],
            "total_distance_m": shared_store["total_distance_m"],
            "total_duration_s": shared_store["total_duration_s"],
        },
    }


def create_stores(
    active_trip: ActiveTripStore | None = None,
    pending_browse_trip: PendingBrowseTripStore | None = None,
    focused_landmark_id: int | None = None,
):
    if pending_browse_trip:
        initial_mode = pending_browse_trip.get("mode") or "explore"
        initial_destinations = pending_browse_trip.get("destination_ids") or []
        initial_active_trip = pending_browse_trip.get("active_trip")
        initial_optimized_trip = pending_browse_trip.get("optimized_trip")
        initial_info = initial_active_info(initial_active_trip)
    elif focused_landmark_id:
        initial_mode = "explore"
        initial_destinations = []
        initial_active_trip = None
        initial_optimized_trip = None
        initial_info = {
            "type": "landmark",
            "content": focused_landmark_id,
        }
    else:
        initial_mode = "trip" if active_trip else "explore"
        initial_destinations = []
        initial_active_trip = active_trip
        initial_optimized_trip = None
        initial_info = initial_active_info(initial_active_trip)

    return [
        dcc.Store(id=ids.DESTINATIONS_LIST, data=initial_destinations),
        dcc.Store(id=ids.MODE_STORE, data=initial_mode),
        dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.SELECTED_TRIP_STORE, data=None),
        dcc.Store(id=ids.ACTIVE_TRIP_STORE, data=initial_active_trip),
        dcc.Store(id=ids.ACTIVE_INFO_STORE, data=initial_info),
        dcc.Store(id=ids.OPTIMIZED_TRIP_STORE, data=initial_optimized_trip),
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
        "",
        id=ids.SHARE_TRIP_TOAST,
        header="",
        icon="info",
        is_open=False,
        dismissable=True,
        duration=3500,
        style={"position": "fixed", "bottom": "4.75rem", "right": "1rem", "zIndex": 9999, "minWidth": "18rem"},
    )


def create_main_content(markers, active_trip=None, focused_landmark=None, lang="bg", guest=False):
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
        style={**CONTENT_STYLE, "marginRight": 0} if guest else CONTENT_STYLE,
        children=[
            dbc.Container(fluid=True, className="h-100 d-flex flex-column p-0", children=[
                dbc.Row(className="h-100 flex-grow-1 p-0", children=[
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    create_map(initial_markers, initial_viewport),
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


def create_authenticated_layout(markers, include_location=True, focused_landmark_id=None, lang="bg", guest=False):
    if is_admin_panel_user(current_user):
        return dcc.Location(id="admin-panel-redirect", href="/admin_panel")
    if not guest and not current_user.is_authenticated:
        return dcc.Location(id="auth-redirect", href="/login")

    registry = LandmarkRegistry.get_landmarks()
    pending_browse_trip = resolve_pending_browse_trip(
        session.pop("pending_browse_trip", None),
        registry=registry,
    )
    focused_landmark = None
    if focused_landmark_id:
        try:
            focused_landmark = registry.get_landmark(int(focused_landmark_id))
        except (TypeError, ValueError, AttributeError):
            focused_landmark = None

    if focused_landmark or guest:
        active_trip = None
    else:
        active_trip = get_active_user_trip(current_user.id)
    children = [
        dcc.Geolocation(id=ids.GEOLOCATION, high_accuracy=True, maximum_age=0, update_now=True, timeout=10000),
        create_sidebar(active_trip, lang=lang, guest=guest),
        create_info_sidebar(lang=lang, guest=guest),
        create_main_content(markers, active_trip, focused_landmark, lang=lang, guest=guest),
        create_landmark_review_pane(lang=lang),
        create_user_menu(fix_to_right=guest, lang=lang, guest=guest),
        *create_stores(active_trip, pending_browse_trip, focused_landmark.id if focused_landmark else None),
        create_warn_modal(lang=lang),
        create_success_toast(lang=lang),
        create_share_trip_toast(lang=lang),
        create_save_trip_modal(lang=lang),
    ]
    if include_location:
        children.insert(0, dcc.Location(id="url"))
    return html.Div(children)


def create_app_layout():
    return html.Div([
        dcc.Location(id="url"),
        dash.page_container,
    ])

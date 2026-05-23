import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import ids
from backend.crud import get_active_user_trip
from callbacks.utils.trip_state import next_action_stop_index
from layout.info_sidebar import create_info_sidebar
from layout.map import create_map
from layout.overlays import create_browse_overlay, create_landmark_review_pane
from layout.sidebar import create_sidebar, create_user_menu
from styles import CONTENT_STYLE


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


def create_stores(active_trip=None):
    initial_mode = "trip" if active_trip else "explore"
    return [
        dcc.Store(id=ids.DESTINATIONS_LIST, data=[]),
        dcc.Store(id=ids.VISIT_ORDER_STORE, data=[]),
        dcc.Store(id=ids.MODE_STORE, data=initial_mode),
        dcc.Store(id=ids.BROWSE_OVERLAY_STORE, data=False),
        dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.BROWSE_VISIT_HISTORY_STORE, data=[]),
        dcc.Store(id=ids.SELECTED_TRIP_STORE, data=None),
        dcc.Store(id=ids.ACTIVE_TRIP_STORE, data=active_trip),
        dcc.Store(id=ids.EXPLORE_MAP_CACHE, data=None),
        dcc.Store(id=ids.ACTIVE_INFO_STORE, data=initial_active_info(active_trip)),
    ]


def create_save_trip_modal():
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Save Trip")),
        dbc.ModalBody([
            dbc.Alert(id=ids.SAVE_TRIP_ALERT, is_open=False, color="danger", duration=4000),
            dbc.Label("Trip name"),
            dbc.Input(id=ids.SAVE_TRIP_NAME_INPUT, placeholder="e.g. Summer Rhodope trip", maxLength=200),
        ]),
        dbc.ModalFooter([
            dbc.Button("Save", id=ids.SAVE_TRIP_CONFIRM_BTN, color="info"),
            dbc.Button("Cancel", id="save-trip-cancel-btn", color="secondary", outline=True, className="ms-2"),
        ]),
    ], id=ids.SAVE_TRIP_MODAL, is_open=False)


def create_warn_modal():
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Cannot optimize route")),
        dbc.ModalBody("Please select at least 2 monuments before optimizing the route."),
        dbc.ModalFooter(dbc.Button("OK", id="warn-modal-close", color="primary")),
    ], id=ids.WARN_MODAL, is_open=False)


def create_success_toast():
    return dbc.Toast(
        "Route Optimized",
        id=ids.SUCCESS_TOAST,
        header="Success!",
        icon="success",
        is_open=False,
        dismissable=True,
        duration=2000,
        style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999, "minWidth": "auto"},
    )


def create_share_trip_toast():
    return dbc.Toast(
        "",
        id=ids.SHARE_TRIP_TOAST,
        header="Share Trip",
        icon="info",
        is_open=False,
        dismissable=True,
        duration=3500,
        style={"position": "fixed", "bottom": "4.75rem", "right": "1rem", "zIndex": 9999, "minWidth": "18rem"},
    )


def create_main_content(markers, active_trip=None):
    initial_markers = [] if active_trip else markers

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
                                    create_map(initial_markers),
                                    create_browse_overlay(),
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


def create_authenticated_layout(markers, include_location=True):
    active_trip = get_active_user_trip(current_user.id)
    children = [
        dcc.Geolocation(id=ids.GEOLOCATION, high_accuracy=True, maximum_age=0, update_now=True, timeout=10000),
        create_sidebar(active_trip),
        create_info_sidebar(),
        create_main_content(markers, active_trip),
        create_landmark_review_pane(),
        create_user_menu(),
        *create_stores(active_trip),
        create_warn_modal(),
        create_success_toast(),
        create_share_trip_toast(),
        create_save_trip_modal(),
    ]
    if include_location:
        children.insert(0, dcc.Location(id="url"))
    return html.Div(children)


def create_app_layout(markers):
    return html.Div([
        dcc.Location(id="url"),
        dash.page_container,
    ])

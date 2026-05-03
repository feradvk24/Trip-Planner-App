import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import ids
from layout.auth import create_login_layout
from layout.map import create_map
from layout.overlays import create_browse_overlay, create_landmark_review_pane
from layout.sidebar import create_sidebar, create_user_menu
from styles import CONTENT_STYLE


def create_stores():
    return [
        dcc.Store(id=ids.DESTINATIONS_LIST, data=[]),
        dcc.Store(id=ids.VISIT_ORDER_STORE, data=[]),
        dcc.Store(id=ids.MODE_STORE, data="explore"),
        dcc.Store(id=ids.BROWSE_OVERLAY_STORE, data=False),
        dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
        dcc.Store(id=ids.ACTIVE_TRIP_STORE, data=None),
        dcc.Store(id=ids.EXPLORE_MAP_CACHE, data=None),
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


def create_main_content(markers):
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
                                    create_map(markers),
                                    create_browse_overlay(),
                                    create_landmark_review_pane(),
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


def create_authenticated_layout(markers):
    return html.Div([
        dcc.Location(id="url"),
        dcc.Geolocation(id=ids.GEOLOCATION, high_accuracy=True, maximum_age=0, update_now=True, timeout=10000),
        create_sidebar(),
        create_main_content(markers),
        create_user_menu(),
        *create_stores(),
        create_warn_modal(),
        create_success_toast(),
        create_share_trip_toast(),
        create_save_trip_modal(),
    ])


def create_app_layout(markers):
    if current_user.is_authenticated:
        return create_authenticated_layout(markers)
    return html.Div([
        dcc.Location(id="url"),
        create_login_layout(),
    ])

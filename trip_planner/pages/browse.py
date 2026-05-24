import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import ids
from backend.crud import get_user_trips
from callbacks.widgets.callback_widgets import build_load_trip_items
from layout.info_sidebar import create_info_sidebar
from layout.sidebar import create_user_menu


dash.register_page(__name__, path_template="/<lang>/browse", name="Browse")


def layout(lang="bg", **kwargs):
    saved_trips = (
        get_user_trips(current_user.id, include_completion_status=True)
        if current_user.is_authenticated else
        []
    )
    return html.Div(
        [
            dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=saved_trips),
            dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
            dcc.Store(id=ids.SELECTED_TRIP_STORE, data=None),
            html.Div(id=ids.SELECTED_OBJECTS_GROUP, style={"display": "none"}),
            create_user_menu(),
            create_info_sidebar(),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Link(
                                [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                                href="/",
                                className="btn btn-outline-secondary btn-sm",
                            ),
                            html.Div(
                                [
                                    html.H2("Browse Trips", className="mb-0"),
                                    html.Div(
                                        "Choose a saved or shared trip to preview its stops.",
                                        className="text-muted",
                                    ),
                                ],
                            ),
                        ],
                        className="d-flex align-items-center gap-3 mb-3",
                    ),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                html.Div(
                                    [
                                        html.Div(
                                            id=ids.FEATURED_LANDMARK_NAME,
                                        ),
                                        html.Div(
                                            html.Img(
                                                id=ids.FEATURED_LANDMARK_IMAGE,
                                                src=None,
                                                alt="Featured landmark",
                                                style={
                                                    "width": "100%",
                                                    "height": "18rem",
                                                    "objectFit": "cover",
                                                    "border": "1px solid #dee2e6",
                                                    "borderRadius": "0.35rem",
                                                    "backgroundColor": "#e9ecef",
                                                    "display": "block",
                                                },
                                            ),
                                            style={
                                                "maxWidth": "52rem",
                                                "backgroundColor": "#ffffff",
                                            },
                                        ),
                                        html.Div(
                                            "Featured landmark details will appear here.",
                                            id=ids.FEATURED_LANDMARK_DESCRIPTION,
                                            className="mt-3",
                                            style={
                                                "maxWidth": "52rem",
                                                "fontSize": "1rem",
                                                "lineHeight": "1.5",
                                            },
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.A(
                                                        "View in map",
                                                        id=ids.FEATURED_LANDMARK_VIEW_MAP,
                                                        href="#",
                                                        className="btn btn-primary",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    html.A(
                                                        "Learn more",
                                                        id=ids.FEATURED_LANDMARK_LINK,
                                                        href="#",
                                                        target="_blank",
                                                        rel="noopener noreferrer",
                                                        className="btn btn-outline-primary",
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            className="mt-3",
                                        )
                                    ],
                                    id=ids.FEATURED_LANDMARK_TAB,
                                    className="p-3",
                                    style={"height": "calc(100vh - 13rem)", "overflowY": "auto"},
                                ),
                                label="Featured",
                                tab_id="featured-landmark",
                            ),
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(
                                        id=ids.LOAD_TRIP_LIST,
                                        children=build_load_trip_items(saved_trips),
                                        flush=True,
                                    ),
                                    id=ids.MY_SAVED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100vh - 13rem)", "overflowY": "auto"},
                                ),
                                label="My Saved Trips",
                                tab_id="my-saved-trips",
                            ),
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.USER_SHARED_TRIPS_LIST, children=[], flush=True),
                                    id=ids.USER_SHARED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100vh - 13rem)", "overflowY": "auto"},
                                ),
                                label="User Shared Trips",
                                tab_id="user-shared-trips",
                            ),
                        ],
                        id=ids.BROWSE_TABS,
                        active_tab="featured-landmark",
                    ),
                ],
                id=ids.PAGE_CONTENT,
                style={
                    "marginRight": "20rem",
                    "height": "100vh",
                    "overflow": "hidden",
                    "padding": "1.5rem",
                    "backgroundColor": "#f8f9fa",
                },
            ),
        ],
    )

import dash_bootstrap_components as dbc
from dash import html, dcc
import ids
from styles import SIDEBAR_STYLE
import dash_leaflet as dl


def create_login_layout():
    return html.Div(
        dbc.Container([
            dbc.Row(dbc.Col(html.H2("Trip Planner Login", className="text-center mb-4"), width=12)),
            dbc.Row(dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Alert(id=ids.LOGIN_ALERT, is_open=False, color="danger", duration=4000),
                    dbc.Label("Username"),
                    dbc.Input(id=ids.LOGIN_USERNAME, placeholder="Enter username", className="mb-3"),
                    dbc.Label("Password"),
                    dbc.Input(id=ids.LOGIN_PASSWORD, type="password", placeholder="Enter password", className="mb-3"),
                    html.Div(id=ids.REGISTER_FIELDS, style={"display": "none"}, children=[
                        dbc.Label("First name"),
                        dbc.Input(id=ids.REGISTER_FIRST_NAME, placeholder="Enter first name", className="mb-3"),
                        dbc.Label("Last name"),
                        dbc.Input(id=ids.REGISTER_LAST_NAME, placeholder="Enter last name", className="mb-3"),
                    ]),
                    dbc.Button("Login", id=ids.LOGIN_BUTTON, color="primary", className="w-100 mb-2"),
                    dbc.Button("Register", id=ids.REGISTER_BUTTON, color="secondary", outline=True, className="w-100"),
                ]), className="shadow"),
                width={"size": 4, "offset": 4},
            )),
        ], className="mt-5"),
        style={"height": "100vh", "backgroundColor": "#f8f9fa"},
    )

def create_selected_object_group():
    return dbc.ListGroup(
        id=ids.SELECTED_OBJECTS_GROUP,
        children=[],
        style={"flex": "1 1 auto", "minHeight": 0, "overflowY": "auto"},
    )

def create_trip_endpoints():
    return html.Div(
        [
            html.Div([
                html.Label("Start:", style={"fontSize": "12px", "marginBottom": "1px"}),
                dbc.Select(
                    options=[{"label": "Автоматично", "value": "auto"}],
                    placeholder="Select a start point",
                    id=ids.START_POINT_DROPDOWN,
                    className="format-dropdown",
                    size=5,
                )
            ]),
            html.Div([
                html.Label("End:", style={"fontSize": "12px", "marginBottom": "1px"}),
                dbc.Select(
                    options=[{"label": "Автоматично", "value": "auto"}],
                    placeholder="Select an end point",
                    id=ids.END_POINT_DROPDOWN,
                    className="format-dropdown",
                    size=5,
                )
            ])
        ],
        style={"marginBottom": 0, "backgroundColor": "#E1E1E1", "border": "1px solid black", "padding": "0.5rem", "borderRadius": "0.25rem"}
    )

def create_sidebar():
    route_endpoints = create_trip_endpoints()
    selected_object_group = create_selected_object_group()
    optimize_route_btn = dbc.Button(
        [html.I(className="bi bi-signpost-split me-2"), "Optimize Route"],
        color="success",
        className="mt-2",
        id=ids.OPTIMIZE_ROUTE_BTN,
    )
    save_trip_btn = dbc.Button(
        [html.I(className="bi bi-save me-2"), "Save Trip"],
        color="secondary",
        className="mt-1",
        id=ids.SAVE_TRIP_BTN,
        disabled=True,
        style={"opacity": "0.45", "flex": "1"},
    )
    load_trip_btn = dbc.Button(
        [html.I(className="bi bi-folder2-open me-2"), "Load Trip"],
        color="info",
        className="mt-1 w-100",
        id=ids.LOAD_TRIP_BTN,
    )
    share_trip_btn = dbc.Button(
        [html.I(className="bi bi-share me-2"), "Share Trip"],
        color="info",
        className="mt-1 w-100",
        id=ids.SHARE_TRIP_BTN,
    )


    mode_toggle = dbc.ButtonGroup(
        [
            dbc.Button("Explore", id=ids.MODE_BTN_EXPLORE, color="primary", outline=True, active=True, size="sm", style={"flex": "1"}),
            dbc.Button("Trip", id=ids.MODE_BTN_TRIP, color="primary", outline=True, active=False, size="sm", style={"flex": "1"}),
            dbc.Button("Browse", id=ids.MODE_BTN_BROWSE, color="primary", outline=True, active=False, size="sm", style={"flex": "1"}),
        ],
        className="w-100",
    )

    explore_panel = html.Div([
        route_endpoints,
        html.Div([
            html.P("Selected monuments:", className="lead", style={"marginBottom": 0}),
            html.Span("Clear all", id=ids.CLEAR_ALL_BTN, style={"fontSize": "0.75rem", "color": "#dc3545", "cursor": "pointer", "userSelect": "none", "alignSelf": "center"}),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}),
        selected_object_group,
        optimize_route_btn,
        html.Div([save_trip_btn], className="d-flex gap-2 w-100"),
    ], id=ids.EXPLORE_PANEL, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0})

    trip_panel = html.Div([
        load_trip_btn,
        html.Div(
            id=ids.TRIP_STATUS_PANEL,
            children=[],
            style={
                "backgroundColor": "#F8F9FA",
                "border": "1px solid #D6D8DB",
                "borderRadius": "0.25rem",
                "padding": "0.75rem",
            },
        ),
        share_trip_btn,
    ], id=ids.TRIP_PANEL, style={"display": "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0})

    browse_panel = html.Div(
        [],
        id=ids.BROWSE_PANEL,
        style={"display": "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0},
    )

    return html.Div([
        html.Div([
            html.Div([
                html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
                html.Span("Bulgarian Monuments", style={"fontSize": "1.25rem", "fontWeight": "600"}),
            ], className="d-flex align-items-center justify-content-center"),
            html.Hr(style={"margin": 0}),
        ], style={"display": "flex", "flexDirection": "column", "gap": "0.25rem"}),
        mode_toggle,
        explore_panel,
        trip_panel,
        browse_panel,
    ], style={**SIDEBAR_STYLE, "gap": "0.5rem"}, id=ids.SIDEBAR)

def create_user_menu():
    return dbc.DropdownMenu(
        id=ids.USER_MENU,
        label=html.I(className="bi bi-person-circle", style={"fontSize": "1.25rem", "color": "black"}),
        children=[
            dbc.DropdownMenuItem("Logout", id=ids.LOGOUT_BUTTON, style={"color": "#dc3545"}),
        ],
        direction="down",
        align_end=True,
        toggle_style={"background": "none", "border": "none", "boxShadow": "none", "padding": "0.25rem 0.5rem", "color": "black"},
        style={
            "position": "fixed",
            "top": "0.75rem",
            "right": "1rem",
            "zIndex": 1050,
        },
    )

def create_map(markers):
    return dl.Map(
        children=[
            dl.TileLayer(),
            dl.Polygon(
                positions=[
                    [[90, -180], [90, 180], [-90, 180], [-90, -180]],
                    [[41.0, 22.0], [41.0, 28.6], [44.3, 28.6], [44.3, 22.0]],
                ],
                color="black",
                fillColor="black",
                fillOpacity=0.6,
                weight=0,
                interactive=False,
            ),
            dl.LayerGroup(id=ids.PLANNED_TRIP_POLYLINE_LAYER),
            dl.LayerGroup(id=ids.LOADED_TRIP_POLYLINE_LAYER),
            dl.LayerGroup(id=ids.USER_LOCATION_LAYER),
            dl.LayerGroup(id=ids.ALL_MARKERS_LAYER, children=markers),
            dl.LayerGroup(id=ids.PLANNED_TRIP_MARKERS_LAYER, children=[]),
            dl.LayerGroup(id=ids.LOADED_TRIP_MARKERS_LAYER, children=[]),
            html.Div(
                id=ids.ROUTE_STATS_PANEL,
                style={
                    "display": "none",
                    "position": "absolute",
                    "bottom": "1.5rem",
                    "left": "1rem",
                    "zIndex": 1000,
                    "background": "rgba(255,255,255,0.92)",
                    "borderRadius": "0.375rem",
                    "padding": "0.5rem 0.75rem",
                    "boxShadow": "0 1px 5px rgba(0,0,0,0.3)",
                    "fontSize": "0.85rem",
                    "lineHeight": "1.6",
                    "pointerEvents": "none",
                },
            ),
        ],
        center=[42.7, 25.0],
        zoom=7.4,
        minZoom=7.4,
        maxBounds=[[41.0, 22.0], [44.3, 28.6]],
        maxBoundsViscosity=1.0,
        zoomSnap=1,
        zoomDelta=0.66,
        wheelPxPerZoomLevel=200,
        zoomAnimation=True,
        style={"width": "100%", "height": "100%"},
    )


def create_browse_overlay():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Browse Trips", className="mb-0"),
                            html.Button(
                                id=ids.BROWSE_CLOSE_BTN,
                                type="button",
                                className="btn-close",
                                **{"aria-label": "Close"},
                            ),
                        ],
                        className="d-flex align-items-center justify-content-between mb-3",
                    ),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.LOAD_TRIP_LIST, children=[], flush=True),
                                    id=ids.MY_SAVED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100% - 3rem)", "overflowY": "auto"},
                                ),
                                label="My Saved Trips",
                                tab_id="my-saved-trips",
                            ),
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.USER_SHARED_TRIPS_LIST, children=[], flush=True),
                                    id=ids.USER_SHARED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100% - 3rem)", "overflowY": "auto"},
                                ),
                                label="User Shared Trips",
                                tab_id="user-shared-trips",
                            ),
                        ],
                        id=ids.BROWSE_TABS,
                        active_tab="my-saved-trips",
                    ),
                ],
                style={
                    "width": "min(58rem, calc(100% - 2rem))",
                    "height": "min(38rem, calc(100% - 2rem))",
                    "backgroundColor": "rgba(255, 255, 255, 0.96)",
                    "border": "1px solid rgba(0, 0, 0, 0.12)",
                    "borderRadius": "0.5rem",
                    "boxShadow": "0 1rem 3rem rgba(0, 0, 0, 0.28)",
                    "padding": "1rem",
                    "overflow": "hidden",
                },
            ),
        ],
        id=ids.BROWSE_OVERLAY,
        style={
            "display": "none",
            "position": "absolute",
            "inset": 0,
            "zIndex": 1000,
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "rgba(248, 249, 250, 0.38)",
            "backdropFilter": "blur(1px)",
            "pointerEvents": "auto",
        },
    )


def create_landmark_review_pane():
    return html.Div(
        [
            dcc.Store(id=ids.LANDMARK_REVIEW_STATE_STORE, data={"is_open": False}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("Leave a review", style={"fontSize": "0.8rem", "color": "#6C757D"}),
                                    html.H4(id=ids.LANDMARK_REVIEW_TITLE, className="mb-0"),
                                    html.Div(
                                        id=ids.LANDMARK_REVIEW_LOCATION,
                                        style={"fontSize": "0.9rem", "color": "#6C757D"},
                                    ),
                                ],
                                style={"minWidth": 0},
                            ),
                            html.Button(
                                id=ids.LANDMARK_REVIEW_CLOSE_BTN,
                                type="button",
                                className="btn-close",
                                **{"aria-label": "Close"},
                            ),
                        ],
                        className="d-flex align-items-start justify-content-between gap-3",
                    ),
                    dbc.Alert(id=ids.LANDMARK_REVIEW_ALERT, is_open=False, color="danger", duration=3500),
                    html.Div(
                        [
                            dbc.Label("Rating", className="mb-1"),
                            html.Div(
                                [
                                    html.Button(
                                        [
                                            html.I(className="bi bi-star-fill"),
                                            html.Span(f"{i} stars", className="visually-hidden"),
                                        ],
                                        id={"type": "landmark-review-star-btn", "index": i},
                                        type="button",
                                        className="landmark-review-star",
                                    )
                                    for i in range(1, 6)
                                ],
                                id=ids.LANDMARK_REVIEW_STAR_ROW,
                                className="landmark-review-stars",
                            ),
                        ],
                        className="d-flex flex-column gap-1",
                    ),
                    html.Div(
                        [
                            dbc.Label("Review", html_for=ids.LANDMARK_REVIEW_TEXT, className="mb-1"),
                            dbc.Textarea(
                                id=ids.LANDMARK_REVIEW_TEXT,
                                placeholder="Share what stood out about this landmark.",
                                maxLength=1000,
                                rows=5,
                            ),
                        ],
                        className="d-flex flex-column gap-1",
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="bi bi-send me-2"), "Submit"],
                                id=ids.LANDMARK_REVIEW_SUBMIT_BTN,
                                color="primary",
                            ),
                            dbc.Button(
                                "Skip",
                                id=ids.LANDMARK_REVIEW_SKIP_BTN,
                                color="secondary",
                                outline=True,
                            ),
                        ],
                        className="d-flex gap-2 justify-content-end",
                    ),
                ],
                style={
                    "width": "min(28rem, calc(100vw - 2rem))",
                    "backgroundColor": "rgba(255, 255, 255, 0.98)",
                    "border": "1px solid rgba(0, 0, 0, 0.12)",
                    "borderRadius": "0.5rem",
                    "boxShadow": "0 1rem 2.5rem rgba(0, 0, 0, 0.25)",
                    "padding": "1rem",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "0.85rem",
                },
            ),
        ],
        id=ids.LANDMARK_REVIEW_PANE,
        style={
            "display": "none",
            "position": "absolute",
            "inset": 0,
            "zIndex": 1001,
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "rgba(248, 249, 250, 0.42)",
            "backdropFilter": "blur(1px)",
            "pointerEvents": "auto",
        },
    )


def create_markers(landmarks, pin_icon, selected_ids=None, selected_icon=None):
    selected_ids = set(selected_ids or [])
    selected_icon = selected_icon or pin_icon
    return [
        dl.Marker(
            position=[l.lat, l.lon],
            children=[
                dl.Tooltip(l.name),
                dl.Popup(html.Div([
                    html.H5(l.name),
                    html.H6(l.location),
                    html.A(
                        "Learn more",
                        href=l.link,
                        target='_blank',
                        style={"display": "block", "text-align": "center"}
                    ),
                    dbc.Button(
                        "Added to trip" if l.id in selected_ids else "Add to trip",
                        id={"type": "add-marker-btn", "index": l.id},
                        color="success",
                        size="sm",
                        className="mt-2 w-100",
                        disabled=l.id in selected_ids,
                    ),
                ]))
            ],
            id={"type": "marker", "index": l.id},
            icon=selected_icon if l.id in selected_ids else pin_icon
        )
        for l in landmarks
    ]

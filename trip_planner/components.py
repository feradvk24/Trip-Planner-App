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

def create_sidebar(route_endpoints, selected_object_group, optimize_route_btn, save_trip_btn, load_trip_btn):
    return html.Div([
        html.Div([
            html.Div([
                html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
                html.Span("Bulgarian Monuments", style={"fontSize": "1.25rem", "fontWeight": "600"}),
            ], className="d-flex align-items-center justify-content-center"),
            html.Hr(style={"margin": 0}),
        ], style={"display": "flex", "flexDirection": "column", "gap": "0.25rem"}),
        route_endpoints,
        html.Div([
            html.P("Selected monuments:", className="lead", style={"marginBottom": 0}),
            html.Span("Clear all", id=ids.CLEAR_ALL_BTN, style={"fontSize": "0.75rem", "color": "#dc3545", "cursor": "pointer", "userSelect": "none", "alignSelf": "center"}),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}),
        selected_object_group,
        optimize_route_btn,
        html.Div([save_trip_btn, load_trip_btn], className="d-flex gap-2 w-100"),
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
            dl.LayerGroup(id="trip-polyline"),
            dl.LayerGroup(id=ids.USER_LOCATION_LAYER),
            dl.LayerGroup(id="all-markers-layer", children=markers),
            dl.LayerGroup(id="tour-markers-layer", children=[]),
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

def create_markers(landmarks, pin_icon):
    import dash_leaflet as dl
    from dash import html
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
                    )
                ]))
            ],
            id={"type": "marker", "index": l.id},
            icon=pin_icon
        )
        for l in landmarks
    ]

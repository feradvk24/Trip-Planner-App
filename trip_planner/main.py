import dash_bootstrap_components as dbc
from dash import Dash, html, dcc
import dash
import dash_leaflet as dl

import ids

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Sidebar styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "borderRight": "1px solid #dee2e6",
}

# Main content styles
CONTENT_STYLE = {
    "marginLeft": "18rem",
    # make the content fill the viewport height and use flex layout so
    # the map can grow to take available space
    "height": "100vh",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
}

# Sidebar component
sidebar = html.Div([
    html.Div([
        html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
        html.Span("Bulgarian Monuments", style={"fontSize": "1.25rem", "fontWeight": "600"}),
    ], className="d-flex align-items-center justify-content-center mb-4"),
    html.Hr(),
], style=SIDEBAR_STYLE, id=ids.SIDEBAR)

# Main content area (simpler: use Bootstrap utilities to manage flex sizing)
content = html.Div(
    id=ids.MAIN_CONTENT,
    style=CONTENT_STYLE,
    children=[
        dbc.Container(fluid=True, className="h-100 d-flex flex-column p-0", children=[
            dbc.Row(className="h-100 flex-grow-1 p-0", children=[
                dbc.Col(
                    [
                        html.H1("Welcome to Trip Planner", className="mb-4", style={"margin-left": "1rem"}),
                        html.P("Select an option from the sidebar to get started.", className="lead", style={"margin-left": "1rem"}),
                        # map wrapper: Bootstrap flex utility lets this fill remaining space
                        html.Div(
                            dl.Map(
                                children=[
                                    dl.TileLayer(),
                                    # mask: big outer polygon with a rectangular hole roughly covering Bulgaria
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
                                ],
                                center=[42.7, 25.0],
                                zoom=7.4,
                                minZoom=7.4,
                                # restrict panning to Bulgaria bounding box (southWest, northEast)
                                maxBounds=[[41.0, 22.0], [44.3, 28.6]],
                                maxBoundsViscosity=1.0,
                                zoomSnap=0.25,
                                zoomDelta=0.25,
                                wheelPxPerZoomLevel=120,
                                zoomAnimation=True,
                                style={"width": "100%", "height": "100%"},
                            ),
                            className="flex-grow-1",
                            style={"minHeight": 0},
                        ),
                    ],
                    width=12,
                    className="d-flex flex-column",
                )
            ])
        ])
    ]
)

# App layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content,
])


if __name__ == "__main__":
    app.run(debug=True)
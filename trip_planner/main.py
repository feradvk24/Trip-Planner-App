import dash_bootstrap_components as dbc
from dash import Dash, Output, html, dcc, Input, State, ALL, ctx
import dash
import dash_leaflet as dl
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from dotenv import load_dotenv
import os

import ids
from marker_config import Landmark, LandmarkRegistry
from backend.tsp_formulas import fetch_route_steps, solve_tsp

load_dotenv()

csv_path = os.getenv("MONUMENTS_CSV")
csv_path = os.path.normpath(csv_path)
monuments_df = pd.read_csv(csv_path)
monuments_df.replace("-", pd.NA, inplace=True)
monuments_df.dropna(subset=['latitude', 'longitude'], inplace=True)

pin_icon = {
    "iconUrl": "/assets/marker-pin.png",
    "iconSize": [30, 30],      # size of the icon
    # "iconAnchor": [15, 40],    # point of the icon which corresponds to marker location
}

checkbox_icon = {
    "iconUrl": "/assets/marker-check.png",
    "iconSize": [30, 30],
    # "iconAnchor": [12, 12],
}
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

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
    "height": "100vh",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
}

landmark_list = [
    Landmark(
        id=index,
        name=row.get('name', 'Monument'),
        location=row.get('location', 'Location'),
        lat=float(row['latitude']),
        lon=float(row['longitude']),
        link=row.get('name_link', '#')
    )
    for index, row in monuments_df.iterrows()
]

# Register them in the singleton
registry = LandmarkRegistry()
registry.register_landmarks(landmark_list)


markers = [
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
    for l in registry.landmarks
]

selected_object_group = dbc.ListGroup(id=ids.SELECTED_OBJECTS_GROUP, children=[], style={"maxHeight": "500px", "overflowY": "auto"})

optimize_route_btn = dbc.Button("Optimize Route", color="primary", className="mt-3", id=ids.OPTIMIZE_ROUTE_BTN)
destinations_list = dcc.Store(id=ids.DESTINATIONS_LIST, data=[])

# Sidebar component
sidebar = html.Div([
    html.Div([
        html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
        html.Span("Bulgarian Monuments", style={"fontSize": "1.25rem", "fontWeight": "600"}),
    ], className="d-flex align-items-center justify-content-center mb-4"),
    html.Hr(),
    html.P("Selected monuments:", className="lead"),
    selected_object_group,
    optimize_route_btn
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
                        # html.H1("Welcome to Trip Planner", className="mb-4", style={"margin-left": "1rem"}),
                        # html.P("Select an option from the sidebar to get started.", className="lead", style={"margin-left": "1rem"}),
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
                                    dl.LayerGroup(id="trip-polyline"),
                                    *markers
                                ],
                                center=[42.7, 25.0],
                                zoom=7.4,
                                minZoom=7.4,
                                # restrict panning to Bulgaria bounding box (southWest, northEast)
                                maxBounds=[[41.0, 22.0], [44.3, 28.6]],
                                maxBoundsViscosity=1.0,
                                zoomSnap=1,
                                zoomDelta=0.66,
                                wheelPxPerZoomLevel=200,
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

@app.callback(
    Output("trip-polyline", "children"),
    Input(ids.OPTIMIZE_ROUTE_BTN, "n_clicks"),
    State(ids.DESTINATIONS_LIST, "data"),
    prevent_initial_call=True
)
def optimize_tsp(n_clicks, destination_ids):
    print("Optimize TSP called")
    print(destination_ids)
    landmarks = registry.get_landmarks(destination_ids)
    visit_order = solve_tsp(landmarks)
    road_segments = fetch_route_steps(visit_order)

    # Choose a colormap
    colormap = cm.get_cmap("viridis", len(road_segments))  # n discrete colors

    # Convert to hex colors for Leaflet
    colors = [mcolors.to_hex(colormap(i)) for i in range(len(road_segments))]

    polylines = [dl.Polyline(positions=segment, color=color, weight=5) for segment, color in zip(road_segments, colors)]
    return polylines


# App layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content,
    destinations_list,
])

@app.callback(
    Output({"type": "marker", "index": ALL}, "icon"),
    Output(ids.SELECTED_OBJECTS_GROUP, "children"),
    Output(ids.DESTINATIONS_LIST, "data"),
    Input({"type": "marker", "index": ALL}, "n_clicks"),
    State(ids.DESTINATIONS_LIST, "data"),
    State(ids.SELECTED_OBJECTS_GROUP, "children"),
    prevent_initial_call=True
)
def toggle_marker(n_clicks_list, selected, current_children):
    if selected is None:
        selected = []
    if current_children is None:
        current_children = []

    landmark_id = ctx.triggered_id["index"]
    landmark = registry.get_landmark(landmark_id)

    # Toggle selection
    if landmark_id in selected:
        selected.remove(landmark_id)
        # Remove ListGroupItem
        current_children = [
            child for child in current_children
            if child["props"]["id"] != f"selected-item-{landmark_id}"
        ]
        icon = pin_icon
    else:
        selected.append(landmark_id)

        # Create UI element using landmark object
        item = dbc.ListGroupItem([
            html.H6(landmark.name, className="mb-1 small"),
            html.P(landmark.location, className="mb-1 small"),
        ],
        className="p-3",
        id=f"selected-item-{landmark_id}")

        current_children.append(item)
        icon = checkbox_icon

    icons = []
    for l in ctx.inputs_list[0]:
        idx = l["id"]["index"]

        if idx == landmark_id:
            icons.append(icon)
        else:
            icons.append(
                checkbox_icon if idx in selected else pin_icon
            )

    return icons, current_children, selected


if __name__ == "__main__":
    app.run(debug=True)
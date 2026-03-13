import dash_bootstrap_components as dbc
from dash import Dash, Output, html, dcc, Input, State, ALL, ctx
import dash
import dash_leaflet as dl
import pandas as pd

from dotenv import load_dotenv
import os

import ids

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

markers = [
    dl.Marker(
        position=[row['latitude'], row['longitude']],
        children=[
            dl.Tooltip(row.get('name', 'Monument')),
            dl.Popup(html.Div([
                html.H5(row.get('name', 'Monument')),
                html.H6(row.get('location', 'Location')),
                html.A("Learn more", href=row.get('name_link', '#'), target='_blank', style={"display": "block", "text-align": "center"}),
            ]))
        ],
        id={"type": "marker", "index": index},
        icon=pin_icon
    )
    for index, row in monuments_df.iterrows()
]

selected_object_group = dbc.ListGroup(id=ids.SELECTED_OBJECTS_GROUP, children=[], style={"maxHeight": "500px", "overflowY": "auto"})

# Sidebar component
sidebar = html.Div([
    html.Div([
        html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
        html.Span("Bulgarian Monuments", style={"fontSize": "1.25rem", "fontWeight": "600"}),
    ], className="d-flex align-items-center justify-content-center mb-4"),
    html.Hr(),
    html.P("Selected monuments:", className="lead"),
    selected_object_group
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

# App layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content,
    dcc.Store(id=ids.DESTINATIONS_LIST, data=[]),
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

    marker_id = ctx.triggered_id["index"]
    row = monuments_df.loc[marker_id]

    # Toggle selection
    if marker_id in selected:
        selected.remove(marker_id)
        # Remove the corresponding ListGroupItem
        current_children = [
            child for child in current_children
            if child["props"]["id"] != f"selected-item-{marker_id}"
        ]
        icon = pin_icon
    else:
        selected.append(marker_id)
        # Append new ListGroupItem
        item = dbc.ListGroupItem([
            html.H6(row.get('name', 'Monument'), className="mb-1 small"),
            html.P(row.get('location', 'Location'), className="mb-1 small"),
        ], className="p-3", id=f"selected-item-{marker_id}")
        current_children.append(item)
        icon = checkbox_icon

    # Update icons: only change clicked marker
    icons = []
    for i, m in enumerate(ctx.inputs_list[0]):
        if m["id"]["index"] == marker_id:
            icons.append(icon)
        else:
            # Keep existing state
            icons.append(checkbox_icon if m["id"]["index"] in selected else pin_icon)

    return icons, current_children, selected


if __name__ == "__main__":
    app.run(debug=True)
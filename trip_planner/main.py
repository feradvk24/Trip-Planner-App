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
from styles import pin_icon, checkbox_icon, SIDEBAR_STYLE, CONTENT_STYLE
from components import create_sidebar, create_trip_endpoints, create_selected_object_group, create_map
from callbacks import register_callbacks
from components import create_markers

load_dotenv()

csv_path = os.getenv("MONUMENTS_CSV")
csv_path = os.path.normpath(csv_path)
monuments_df = pd.read_csv(csv_path)
monuments_df.replace("-", pd.NA, inplace=True)
monuments_df.dropna(subset=['latitude', 'longitude'], inplace=True)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

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


markers = create_markers(registry.landmarks, pin_icon)

# Use component functions
selected_object_group = create_selected_object_group()
trip_endpoints = create_trip_endpoints()

optimize_route_btn = dbc.Button("Optimize Route", color="primary", className="mt-2", id=ids.OPTIMIZE_ROUTE_BTN)
destinations_list = dcc.Store(id=ids.DESTINATIONS_LIST, data=[])

# Sidebar component
sidebar = create_sidebar(trip_endpoints, selected_object_group, optimize_route_btn)

# Main content area (simpler: use Bootstrap utilities to manage flex sizing)
content = html.Div(
    id=ids.MAIN_CONTENT,
    style=CONTENT_STYLE,
    children=[
        dbc.Container(fluid=True, className="h-100 d-flex flex-column p-0", children=[
            dbc.Row(className="h-100 flex-grow-1 p-0", children=[
                dbc.Col(
                    [
                        html.Div(
                            create_map(markers),
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

warn_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Cannot optimize route")),
    dbc.ModalBody("Please select at least 2 monuments before optimizing the route."),
    dbc.ModalFooter(dbc.Button("OK", id="warn-modal-close", color="primary")),
], id=ids.WARN_MODAL, is_open=False)

# App layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content,
    destinations_list,
    warn_modal,
])

register_callbacks(app, registry)

if __name__ == "__main__":
    app.run(debug=True)
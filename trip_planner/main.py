import dash_bootstrap_components as dbc
from dash import Dash, Output, html, dcc, Input, State, ALL, ctx
import dash
import dash_leaflet as dl
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from flask import Flask, redirect, request, session
from flask_login import current_user, logout_user

from dotenv import load_dotenv
import os

import ids
from marker_config import Landmark, LandmarkRegistry
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon, SIDEBAR_STYLE, CONTENT_STYLE
from components import (
    create_sidebar, create_trip_endpoints, create_selected_object_group,
    create_map, create_login_layout, create_markers, create_user_menu,
)
from callbacks import register_callbacks
from auth import init_login_manager

load_dotenv()

csv_path = os.getenv("MONUMENTS_CSV")
csv_path = os.path.normpath(csv_path)
monuments_df = pd.read_csv(csv_path)
monuments_df.replace("-", pd.NA, inplace=True)
monuments_df.dropna(subset=['latitude', 'longitude'], inplace=True)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

# Initialize Flask-Login
init_login_manager(server)

# Protect all Dash views — redirect unauthenticated users to /login
@server.before_request
def require_login():
    # Allow static assets, the login page itself, and Dash's internal routes
    allowed_paths = {"/login", "/_dash-layout", "/_dash-dependencies", "/_reload-hash"}
    if (
        request.path.startswith("/assets/")
        or request.path.startswith("/_dash-update-component")
        or request.path in allowed_paths
    ):
        return
    if not current_user.is_authenticated:
        return redirect("/login")

@server.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect("/login")

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

success_toast = dbc.Toast(
    "Route Optimized",
    id=ids.SUCCESS_TOAST,
    header="Success!",
    icon="success",
    is_open=False,
    dismissable=True,
    duration=2000,
    style={"position": "fixed", "bottom": "1rem", "right": "1rem", "zIndex": 9999, "minWidth": "auto"},
)

# App layout — dynamic: shows login form or main app based on auth state
def serve_layout():
    if current_user.is_authenticated:
        return html.Div([
            dcc.Location(id="url"),
            dcc.Geolocation(id=ids.GEOLOCATION, high_accuracy=True, maximum_age=0),
            sidebar,
            content,
            create_user_menu(),
            destinations_list,
            warn_modal,
            success_toast,
        ])
    return html.Div([
        dcc.Location(id="url"),
        create_login_layout(),
    ])

app.layout = serve_layout

register_callbacks(app, registry)

if __name__ == "__main__":
    app.run(debug=True)
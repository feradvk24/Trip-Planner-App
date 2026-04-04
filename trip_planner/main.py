import dash_bootstrap_components as dbc
from dash import Dash, Output, html, dcc, Input, State, ALL, ctx
import dash
import dash_leaflet as dl
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from flask import Flask, redirect, request, session
from flask_login import current_user, logout_user

from dotenv import load_dotenv
import os

load_dotenv()

import ids
from marker_config import Landmark, LandmarkRegistry
from backend.tsp_formulas import fetch_route_steps, solve_tsp
from styles import pin_icon, checkbox_icon, SIDEBAR_STYLE, CONTENT_STYLE
from components import (
    create_sidebar, create_trip_endpoints, create_selected_object_group,
    create_map, create_login_layout, create_markers, create_user_menu,
)
from callbacks import register_callbacks
from backend.auth import init_login_manager
from backend.database import init_db, shutdown_session, SessionLocal, create_database_if_missing
from backend.models import Landmark as LandmarkModel

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

# Initialize Flask-Login
init_login_manager(server)

# Initialize database (creates the DB and tables if they don't exist)
create_database_if_missing()
init_db()
server.teardown_appcontext(shutdown_session)

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

db = SessionLocal()
try:
    db_landmarks = db.query(LandmarkModel).all()
    landmark_list = [
        Landmark(
            id=row.id,
            name=row.name,
            location=row.location or 'Location',
            lat=row.latitude,
            lon=row.longitude,
            link=row.link or '#'
        )
        for row in db_landmarks
    ]
finally:
    db.close()

# Register them in the singleton
registry = LandmarkRegistry()
registry.register_landmarks(landmark_list)


markers = create_markers(registry.landmarks, pin_icon)

# Use component functions
selected_object_group = create_selected_object_group()
trip_endpoints = create_trip_endpoints()

optimize_route_btn = dbc.Button("Optimize Route", color="primary", className="mt-2", id=ids.OPTIMIZE_ROUTE_BTN)
save_trip_btn = dbc.Button("Save Trip", color="secondary", className="mt-1", id=ids.SAVE_TRIP_BTN, disabled=True, style={"opacity": "0.45"})
load_trip_btn = dbc.Button("Load Trip", color="primary", outline=True, className="mt-1", id=ids.LOAD_TRIP_BTN)
destinations_list = dcc.Store(id=ids.DESTINATIONS_LIST, data=[])
visit_order_store = dcc.Store(id=ids.VISIT_ORDER_STORE, data=[])

save_trip_modal = dbc.Modal([
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

load_trip_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Load Trip")),
    dbc.ModalBody(
        dbc.ListGroup(id=ids.LOAD_TRIP_LIST, children=[], flush=True),
        style={"maxHeight": "60vh", "overflowY": "auto"},
    ),
], id=ids.LOAD_TRIP_MODAL, is_open=False, centered=True, scrollable=True)

# Sidebar component
sidebar = create_sidebar(trip_endpoints, selected_object_group, optimize_route_btn, save_trip_btn, load_trip_btn)

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
            visit_order_store,
            warn_modal,
            success_toast,
            save_trip_modal,
            load_trip_modal,
        ])
    return html.Div([
        dcc.Location(id="url"),
        create_login_layout(),
    ])

app.layout = serve_layout

register_callbacks(app, registry)

if __name__ == "__main__":
    app.run(debug=True)
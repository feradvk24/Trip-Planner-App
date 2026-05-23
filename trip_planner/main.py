import dash_bootstrap_components as dbc
from dash import Dash
from flask import redirect, request
from flask_login import current_user, logout_user
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import app_context
from backend.api_routes import register_api_routes
from backend.auth import init_login_manager
from backend.database import create_database_if_missing, init_db, shutdown_session
from backend.landmark_registry import LandmarkRegistry
from callbacks import register_callbacks
from layout.app_layout import create_app_layout
from layout.markers import create_markers
from styles import pin_icon

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder=str(Path(__file__).parent / "pages"),
)
server = app.server

# Initialize Flask-Login
init_login_manager(server)

# Initialize database (creates the DB and tables if they don't exist)
create_database_if_missing()
init_db()
server.teardown_appcontext(shutdown_session)


# Protect all Dash views - redirect unauthenticated users to /login
@server.before_request
def require_login():
    # Allow static assets, the login page itself, and Dash's internal routes
    allowed_paths = {"/login", "/_dash-layout", "/_dash-dependencies", "/_reload-hash"}
    if (
        request.path.startswith("/assets/")
        or request.path.startswith("/_dash-component-suites/")
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


registry = LandmarkRegistry.from_database()
register_api_routes(server, registry)
markers = create_markers(registry.landmarks, pin_icon)
app_context.REGISTRY = registry
app_context.MARKERS = markers
app.layout = lambda: create_app_layout(markers)

register_callbacks(app, registry)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

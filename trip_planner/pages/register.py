import dash
from dash import dcc
from flask_login import current_user, logout_user

from trip_planner.backend.auth import is_admin_panel_user
from trip_planner.layout.auth import create_register_layout


dash.register_page(__name__, path="/register", name="Register", order=-90)


def layout(**kwargs):
    if current_user.is_authenticated:
        if is_admin_panel_user(current_user):
            logout_user()
            return create_register_layout()
        return dcc.Location(id="register-redirect", href="/bg")
    return create_register_layout()

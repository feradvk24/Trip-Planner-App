import dash
from dash import dcc
from flask import request
from flask_login import current_user, logout_user

from trip_planner.backend.auth import is_admin_panel_user, is_valid_password_reset_token
from trip_planner.layout.auth import create_login_layout


dash.register_page(__name__, path="/login", name="Login", order=-100)


def layout(**kwargs):
    password_reset_token = kwargs.get("password_reset_token") or request.args.get("password_reset_token")
    if password_reset_token:
        if current_user.is_authenticated:
            logout_user()
        return create_login_layout(
            password_reset_token_valid=is_valid_password_reset_token(password_reset_token)
        )

    if current_user.is_authenticated:
        if not is_admin_panel_user(current_user):
            return dcc.Location(id="login-redirect", href="/bg")
    return create_login_layout()

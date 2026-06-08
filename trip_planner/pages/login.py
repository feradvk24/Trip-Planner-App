import dash
from dash import dcc
from flask_login import current_user

from backend.auth import is_admin_panel_user
from layout.auth import create_login_layout


dash.register_page(__name__, path="/login", name="Login", order=-100)


def layout(**kwargs):
    if current_user.is_authenticated:
        if not is_admin_panel_user(current_user):
            return dcc.Location(id="login-redirect", href="/bg")
    return create_login_layout()

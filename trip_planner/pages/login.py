import dash
from dash import dcc
from flask_login import current_user

from layout.auth import create_login_layout


dash.register_page(__name__, path="/login", name="Login")


def layout(**kwargs):
    if current_user.is_authenticated:
        return dcc.Location(id="login-redirect", href="/bg")
    return create_login_layout()

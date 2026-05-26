import dash
from dash import dcc
from flask_login import current_user

from layout.auth import create_register_layout


dash.register_page(__name__, path="/register", name="Register", order=-90)


def layout(**kwargs):
    if current_user.is_authenticated:
        return dcc.Location(id="register-redirect", href="/bg")
    return create_register_layout()

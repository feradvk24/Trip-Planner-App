import dash
from dash import dcc, html
from flask_login import current_user

from i18n import DEFAULT_LANGUAGE


dash.register_page(__name__, path="/admin_panel", name="Admin Panel", order=0)


def layout(**kwargs):
    if not current_user.is_authenticated:
        return dcc.Location(id="admin-login-redirect", href="/login")
    if getattr(current_user, "role", "regular") != "admin":
        return dcc.Location(id="admin-home-redirect", href=f"/{DEFAULT_LANGUAGE}")
    return html.Div()

import dash
from dash import dcc
from flask_login import current_user

from admin.layout import create_admin_layout
from i18n import DEFAULT_LANGUAGE


dash.register_page(__name__, path="/admin_panel", name="Admin Panel", order=0)


def layout(**kwargs):
    if not current_user.is_authenticated:
        return dcc.Location(id="admin-login-redirect", href="/login")
    role = getattr(current_user, "role", "regular")
    if role not in {"admin", "moderator"}:
        return dcc.Location(id="admin-home-redirect", href=f"/{DEFAULT_LANGUAGE}")
    return create_admin_layout(role=role)

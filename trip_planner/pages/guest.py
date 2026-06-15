import dash
from dash import dcc
from flask_login import current_user

from trip_planner.backend.auth import is_admin_panel_user
from trip_planner.services.landmark_registry import LandmarkRegistry
from trip_planner.layout.app_layout import create_authenticated_layout
from trip_planner.layout.markers import create_markers
from trip_planner.styles import pin_icon


dash.register_page(__name__, path="/guest", name="Guest", order=-90)


def layout(**kwargs):
    if is_admin_panel_user(current_user):
        return dcc.Location(id="guest-admin-redirect", href="/admin_panel")

    registry = LandmarkRegistry.get_landmarks("bg")
    markers = create_markers(registry.landmarks, pin_icon, lang="bg", allow_add_to_trip=False)
    return create_authenticated_layout(
        markers,
        include_location=False,
        lang="bg",
        guest=True,
    )

import dash

from services.landmark_registry import LandmarkRegistry
from layout.app_layout import create_authenticated_layout
from layout.markers import create_markers
from styles import pin_icon


dash.register_page(__name__, path="/guest", name="Guest", order=-90)


def layout(**kwargs):
    registry = LandmarkRegistry.get_landmarks()
    markers = create_markers(registry.landmarks, pin_icon, lang="bg", allow_add_to_trip=False)
    return create_authenticated_layout(
        markers,
        include_location=False,
        lang="bg",
        guest=True,
    )

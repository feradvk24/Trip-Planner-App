import dash

from backend.landmark_registry import LandmarkRegistry
from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from layout.app_layout import create_authenticated_layout
from layout.markers import create_markers
from styles import pin_icon


dash.register_page(__name__, path_template="/<lang>", name="Map", order=100)


def layout(lang="bg", focus_landmark=None, **kwargs):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    registry = LandmarkRegistry.get_landmarks()
    markers = create_markers(registry.landmarks, pin_icon, lang=lang)
    return create_authenticated_layout(
        markers,
        include_location=False,
        focused_landmark_id=focus_landmark,
        lang=lang,
    )

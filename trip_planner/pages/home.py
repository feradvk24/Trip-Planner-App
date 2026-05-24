import dash

import app_context
from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from layout.app_layout import create_authenticated_layout


dash.register_page(__name__, path_template="/<lang>", name="Map", order=100)


def layout(lang="bg", focus_landmark=None, **kwargs):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    return create_authenticated_layout(
        app_context.MARKERS,
        include_location=False,
        focused_landmark_id=focus_landmark,
        lang=lang,
    )

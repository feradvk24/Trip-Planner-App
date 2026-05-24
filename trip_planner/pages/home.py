import dash

import app_context
from layout.app_layout import create_authenticated_layout


dash.register_page(__name__, path_template="/<lang>/", name="Map")


def layout(lang="bg", focus_landmark=None, **kwargs):
    return create_authenticated_layout(
        app_context.MARKERS,
        include_location=False,
        focused_landmark_id=focus_landmark,
        lang=lang,
    )

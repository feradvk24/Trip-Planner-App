import dash

import app_context
from layout.app_layout import create_authenticated_layout


dash.register_page(__name__, path="/", name="Map")


def layout(**kwargs):
    return create_authenticated_layout(app_context.MARKERS, include_location=False)

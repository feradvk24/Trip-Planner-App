from callbacks.auth import register_auth_callbacks
from callbacks.browse import register_browse_callbacks
from callbacks.explore import register_explore_callbacks
from callbacks.reviews import register_review_callbacks
from callbacks.trip import register_trip_callbacks
from callbacks.view import register_view_callbacks


def register_callbacks(app, registry):
    register_auth_callbacks(app)
    register_explore_callbacks(app, registry)
    register_view_callbacks(app, registry)
    register_browse_callbacks(app, registry)
    register_trip_callbacks(app, registry)
    register_review_callbacks(app)

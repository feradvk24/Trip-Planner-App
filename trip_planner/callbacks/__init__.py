from trip_planner.callbacks.auth import register_auth_callbacks
from trip_planner.callbacks.browse import register_browse_callbacks
from trip_planner.callbacks.explore import register_explore_callbacks
from trip_planner.callbacks.info import register_info_callbacks
from trip_planner.callbacks.reviews import register_review_callbacks
from trip_planner.callbacks.trip import register_trip_callbacks
from trip_planner.callbacks.view import register_view_callbacks
from trip_planner.admin.callbacks import register_admin_callbacks


def register_callbacks(app):
    register_auth_callbacks(app)
    register_explore_callbacks(app)
    register_info_callbacks(app)
    register_view_callbacks(app)
    register_browse_callbacks(app)
    register_trip_callbacks(app)
    register_review_callbacks(app)
    register_admin_callbacks(app)

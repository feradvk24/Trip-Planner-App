import dash_bootstrap_components as dbc
from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
from flask_login import current_user

from admin import ids
from admin.crud import (
    delete_review,
    get_recent_reviews,
    get_reviews_by_username,
    get_user_role,
    set_user_role,
)
from admin.layout import _build_review_list, _build_user_role_details


ADMIN_PANEL_ROLES = {"admin", "moderator"}


def register_admin_callbacks(app):
    @app.callback(
        Output(ids.ADMIN_USER_REVIEWS_LIST, "children"),
        Input(ids.ADMIN_REVIEW_USER_SEARCH_BUTTON, "n_clicks"),
        State(ids.ADMIN_REVIEW_USER_SEARCH_INPUT, "value"),
        prevent_initial_call=True,
    )
    def search_user_reviews(n_clicks, username):
        if not n_clicks:
            raise PreventUpdate
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") not in ADMIN_PANEL_ROLES:
            return dbc.ListGroupItem("Admin access required.", className="text-danger")

        username = (username or "").strip()
        if not username:
            return dbc.ListGroupItem("Enter a username to search.", className="text-muted")

        reviews = get_reviews_by_username(username, limit=100)
        return _build_review_list(reviews, f"No reviews found for {username}.")

    @app.callback(
        Output(ids.ADMIN_RECENT_REVIEWS_LIST, "children"),
        Output(ids.ADMIN_USER_REVIEWS_LIST, "children", allow_duplicate=True),
        Output(ids.ADMIN_DELETE_REVIEW_ALERT, "children"),
        Output(ids.ADMIN_DELETE_REVIEW_ALERT, "color"),
        Output(ids.ADMIN_DELETE_REVIEW_ALERT, "is_open"),
        Input(ids.ADMIN_DELETE_REVIEW_BUTTON, "n_clicks"),
        State(ids.ADMIN_DELETE_REVIEW_ID_INPUT, "value"),
        State(ids.ADMIN_REVIEW_USER_SEARCH_INPUT, "value"),
        prevent_initial_call=True,
    )
    def delete_review_by_id(n_clicks, review_id, searched_username):
        if not n_clicks:
            raise PreventUpdate
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") not in ADMIN_PANEL_ROLES:
            return no_update, no_update, "Admin access required.", "danger", True
        if not review_id:
            return no_update, no_update, "Enter a review ID to delete.", "danger", True

        deleted = delete_review(int(review_id))
        recent_reviews = get_recent_reviews(limit=100)
        recent_children = _build_review_list(recent_reviews, "No reviews found.")

        searched_username = (searched_username or "").strip()
        if searched_username:
            user_reviews = get_reviews_by_username(searched_username, limit=100)
            user_children = _build_review_list(user_reviews, f"No reviews found for {searched_username}.")
        else:
            user_children = dbc.ListGroupItem(
                "Search for a user to display their reviews.",
                className="text-muted",
            )

        if not deleted:
            return recent_children, user_children, f"Review #{review_id} was not found.", "warning", True
        return recent_children, user_children, f"Review #{review_id} deleted.", "success", True

    @app.callback(
        Output(ids.ADMIN_ROLE_USER_DETAILS, "children"),
        Output(ids.ADMIN_ROLE_ALERT, "children"),
        Output(ids.ADMIN_ROLE_ALERT, "color"),
        Output(ids.ADMIN_ROLE_ALERT, "is_open"),
        Input(ids.ADMIN_ROLE_SEARCH_BUTTON, "n_clicks"),
        State(ids.ADMIN_ROLE_USERNAME_INPUT, "value"),
        prevent_initial_call=True,
    )
    def search_user_role(n_clicks, username):
        if not n_clicks:
            raise PreventUpdate
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") != "admin":
            return no_update, "Only admins can edit user roles.", "danger", True

        username = (username or "").strip()
        if not username:
            return _build_user_role_details(None, "Enter a username to search."), "", "info", False

        user = get_user_role(username)
        if user is None:
            return _build_user_role_details(None, f"No user found for {username}."), "", "info", False
        return _build_user_role_details(user), "", "info", False

    @app.callback(
        Output(ids.ADMIN_ROLE_USER_DETAILS, "children", allow_duplicate=True),
        Output(ids.ADMIN_ROLE_ALERT, "children", allow_duplicate=True),
        Output(ids.ADMIN_ROLE_ALERT, "color", allow_duplicate=True),
        Output(ids.ADMIN_ROLE_ALERT, "is_open", allow_duplicate=True),
        Input(ids.ADMIN_SET_MODERATOR_BUTTON, "n_clicks"),
        Input(ids.ADMIN_SET_REGULAR_BUTTON, "n_clicks"),
        State(ids.ADMIN_ROLE_USERNAME_INPUT, "value"),
        prevent_initial_call=True,
    )
    def set_user_role_from_button(moderator_clicks, regular_clicks, username):
        if not moderator_clicks and not regular_clicks:
            raise PreventUpdate
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") != "admin":
            return no_update, no_update, no_update, False

        username = (username or "").strip()
        if not username:
            return no_update, no_update, no_update, False

        target_role = (
            "moderator"
            if ctx.triggered_id == ids.ADMIN_SET_MODERATOR_BUTTON
            else "regular"
        )

        existing_user = get_user_role(username)
        if existing_user is None:
            return no_update, no_update, no_update, False
        if existing_user["role"] == "admin":
            return no_update, no_update, no_update, False
        if existing_user["role"] == target_role:
            return no_update, no_update, no_update, False

        user = set_user_role(username, target_role)
        if user is None:
            return no_update, no_update, no_update, False
        return _build_user_role_details(user), f"{user['username']} is now {target_role}.", "success", True

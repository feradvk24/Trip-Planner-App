import dash_bootstrap_components as dbc
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from flask_login import current_user

from admin import ids
from admin.crud import delete_review, get_recent_reviews, get_reviews_by_username
from admin.layout import _build_review_list


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
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") != "admin":
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
        if not current_user.is_authenticated or getattr(current_user, "role", "regular") != "admin":
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

import dash_bootstrap_components as dbc
from dash import dcc, html

from admin import ids
from admin.crud import get_recent_reviews


def _build_review_item(review: dict):
    review_text = review.get("review_text") or "No written review."
    return dbc.ListGroupItem(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(f"#{review['id']}", className="fw-semibold"),
                            html.Span(f"{review['rating']}/5", className="badge text-bg-secondary"),
                        ],
                        className="d-flex align-items-center gap-2",
                    ),
                    html.Small(review["created_at"], className="text-muted"),
                ],
                className="d-flex justify-content-between gap-3",
            ),
            html.Div(review["landmark_name"], className="fw-semibold mt-2"),
            html.Div(
                f"{review['user_name']} ({review['username']})",
                className="text-muted small",
            ),
            html.Div(review_text, className="mt-2"),
        ]
    )


def _build_review_list(reviews: list[dict], empty_message: str):
    if not reviews:
        return dbc.ListGroupItem(empty_message, className="text-muted")
    return [_build_review_item(review) for review in reviews]


def create_reviews_tab():
    recent_reviews = get_recent_reviews(limit=100)
    return html.Div(
        [
            html.Div(
                [
                    html.H4("Recent reviews", className="mb-3"),
                    dbc.ListGroup(
                        id=ids.ADMIN_RECENT_REVIEWS_LIST,
                        children=_build_review_list(recent_reviews, "No reviews found."),
                        flush=True,
                        style={"maxHeight": "calc(100dvh - 13rem)", "overflowY": "auto"},
                    ),
                ],
                className="border rounded p-3",
                style={"flex": "2 1 34rem", "minWidth": "20rem"},
            ),
            html.Div(
                [
                    html.H4("Search user reviews", className="mb-3"),
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id=ids.ADMIN_REVIEW_USER_SEARCH_INPUT,
                                placeholder="Username",
                                type="text",
                            ),
                            dbc.Button(
                                "Search",
                                id=ids.ADMIN_REVIEW_USER_SEARCH_BUTTON,
                                color="primary",
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.ListGroup(
                        id=ids.ADMIN_USER_REVIEWS_LIST,
                        children=[
                            dbc.ListGroupItem(
                                "Search for a user to display their reviews.",
                                className="text-muted",
                            )
                        ],
                        flush=True,
                        style={"maxHeight": "calc(100dvh - 18rem)", "overflowY": "auto"},
                    ),
                ],
                className="border rounded p-3",
                style={"flex": "1 1 24rem", "minWidth": "20rem"},
            ),
            html.Div(
                [
                    html.H4("Delete review", className="mb-3"),
                    dbc.Alert(id=ids.ADMIN_DELETE_REVIEW_ALERT, is_open=False, color="danger"),
                    dbc.Label("Review ID"),
                    dbc.Input(
                        id=ids.ADMIN_DELETE_REVIEW_ID_INPUT,
                        placeholder="Review ID",
                        type="number",
                        min=1,
                        step=1,
                    ),
                    dbc.Button(
                        "Delete",
                        id=ids.ADMIN_DELETE_REVIEW_BUTTON,
                        color="danger",
                        className="mt-3",
                    ),
                ],
                className="border rounded p-3",
                style={"flex": "0 1 18rem", "minWidth": "16rem"},
            ),
        ],
        className="d-flex flex-wrap gap-3",
    )


def _build_user_role_details(user: dict | None, empty_message="Search for a user to display their role."):
    if not user:
        return dbc.ListGroupItem(empty_message, className="text-muted")
    return dbc.ListGroupItem(
        [
            html.Div(user["username"], className="fw-semibold"),
            html.Div(user["user_name"], className="text-muted small"),
            html.Div(f"Current role: {user['role']}", className="mt-2"),
        ]
    )


def create_user_roles_tab():
    return html.Div(
        [
            html.Div(
                [
                    html.H4("Edit user role", className="mb-3"),
                    dbc.Alert(id=ids.ADMIN_ROLE_ALERT, is_open=False, color="info"),
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id=ids.ADMIN_ROLE_USERNAME_INPUT,
                                placeholder="Username",
                                type="text",
                            ),
                            dbc.Button(
                                "Search",
                                id=ids.ADMIN_ROLE_SEARCH_BUTTON,
                                color="primary",
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.ListGroup(
                        id=ids.ADMIN_ROLE_USER_DETAILS,
                        children=_build_user_role_details(None),
                        flush=True,
                        className="mb-3",
                    ),
                    dbc.Label("Set role"),
                    html.Div(
                        [
                            dbc.Button(
                                "Moderator",
                                id=ids.ADMIN_SET_MODERATOR_BUTTON,
                                color="warning",
                            ),
                            dbc.Button(
                                "Regular",
                                id=ids.ADMIN_SET_REGULAR_BUTTON,
                                color="secondary",
                                outline=True,
                            ),
                        ],
                        className="d-flex gap-2",
                    ),
                ],
                className="border rounded p-3",
                style={"maxWidth": "36rem"},
            ),
        ]
    )


def create_admin_layout(role="regular"):
    tabs = [
        dbc.Tab(
            create_reviews_tab(),
            label="Reviews",
            tab_id="reviews",
            className="pt-3",
        ),
    ]
    if role == "admin":
        tabs.append(
            dbc.Tab(
                create_user_roles_tab(),
                label="Users",
                tab_id="users",
                className="pt-3",
            )
        )

    return html.Div(
        [
            html.H2("Admin Panel", className="mb-4"),
            dbc.Tabs(
                tabs,
                id=ids.ADMIN_TABS,
                active_tab="reviews",
            ),
        ],
        className="p-4",
        style={"minHeight": "100dvh", "backgroundColor": "#f8f9fa"},
    )

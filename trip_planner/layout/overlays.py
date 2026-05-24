import dash_bootstrap_components as dbc
from dash import dcc, html

import ids
from i18n import t

def create_browse_overlay(lang="bg"):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4(t("browse_overlay.title", lang=lang), className="mb-0"),
                            html.Button(
                                id=ids.BROWSE_CLOSE_BTN,
                                type="button",
                                className="btn-close",
                                **{"aria-label": "Close"},
                            ),
                        ],
                        className="d-flex align-items-center justify-content-between mb-3",
                    ),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.LOAD_TRIP_LIST, children=[], flush=True),
                                    id=ids.MY_SAVED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100% - 3rem)", "overflowY": "auto"},
                                ),
                                label=t("browse_overlay.my_saved_trips", lang=lang),
                                tab_id="my-saved-trips",
                            ),
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.USER_SHARED_TRIPS_LIST, children=[], flush=True),
                                    id=ids.USER_SHARED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100% - 3rem)", "overflowY": "auto"},
                                ),
                                label=t("browse_overlay.user_shared_trips", lang=lang),
                                tab_id="user-shared-trips",
                            ),
                        ],
                        id=ids.BROWSE_TABS,
                        active_tab="my-saved-trips",
                    ),
                ],
                style={
                    "width": "min(58rem, calc(100% - 2rem))",
                    "height": "min(38rem, calc(100% - 2rem))",
                    "backgroundColor": "rgba(255, 255, 255, 0.96)",
                    "border": "1px solid rgba(0, 0, 0, 0.12)",
                    "borderRadius": "0.5rem",
                    "boxShadow": "0 1rem 3rem rgba(0, 0, 0, 0.28)",
                    "padding": "1rem",
                    "overflow": "hidden",
                },
            ),
        ],
        id=ids.BROWSE_OVERLAY,
        style={
            "display": "none",
            "position": "absolute",
            "inset": 0,
            "zIndex": 1000,
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "rgba(248, 249, 250, 0.38)",
            "backdropFilter": "blur(1px)",
            "pointerEvents": "auto",
        },
    )


def create_landmark_review_pane(lang="bg"):
    return html.Div(
        [
            dcc.Store(id=ids.LANDMARK_REVIEW_STATE_STORE, data={"is_open": False}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        t("landmark_review.eyebrow", lang=lang),
                                        id=ids.LANDMARK_REVIEW_EYEBROW,
                                        style={"fontSize": "0.8rem", "color": "#6C757D"},
                                    ),
                                    html.H4(id=ids.LANDMARK_REVIEW_TITLE, className="mb-0"),
                                    html.Div(
                                        id=ids.LANDMARK_REVIEW_LOCATION,
                                        style={"fontSize": "0.9rem", "color": "#6C757D"},
                                    ),
                                ],
                                style={"minWidth": 0},
                            ),
                            html.Button(
                                id=ids.LANDMARK_REVIEW_CLOSE_BTN,
                                type="button",
                                className="btn-close",
                                **{"aria-label": "Close"},
                            ),
                        ],
                        className="d-flex align-items-start justify-content-between gap-3",
                    ),
                    dbc.Alert(id=ids.LANDMARK_REVIEW_ALERT, is_open=False, color="danger", duration=3500),
                    html.Div(
                        [
                            dbc.Label(t("landmark_review.rating", lang=lang), className="mb-1"),
                            html.Div(
                                [
                                    html.Button(
                                        [
                                            html.I(className="bi bi-star-fill"),
                                            html.Span(f"{i} stars", className="visually-hidden"),
                                        ],
                                        id={"type": "landmark-review-star-btn", "index": i},
                                        type="button",
                                        className="landmark-review-star",
                                    )
                                    for i in range(1, 6)
                                ],
                                id=ids.LANDMARK_REVIEW_STAR_ROW,
                                className="landmark-review-stars",
                            ),
                        ],
                        className="d-flex flex-column gap-1",
                    ),
                    html.Div(
                        [
                            dbc.Label(t("landmark_review.review", lang=lang), html_for=ids.LANDMARK_REVIEW_TEXT, className="mb-1"),
                            dbc.Textarea(
                                id=ids.LANDMARK_REVIEW_TEXT,
                                placeholder=t("landmark_review.placeholder", lang=lang),
                                maxLength=1000,
                                rows=5,
                            ),
                        ],
                        className="d-flex flex-column gap-1",
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="bi bi-send me-2"), t("landmark_review.submit", lang=lang)],
                                id=ids.LANDMARK_REVIEW_SUBMIT_BTN,
                                color="primary",
                            ),
                            dbc.Button(
                                t("landmark_review.skip", lang=lang),
                                id=ids.LANDMARK_REVIEW_SKIP_BTN,
                                color="secondary",
                                outline=True,
                            ),
                        ],
                        className="d-flex gap-2 justify-content-end",
                    ),
                ],
                style={
                    "width": "min(28rem, calc(100vw - 2rem))",
                    "backgroundColor": "rgba(255, 255, 255, 0.98)",
                    "border": "1px solid rgba(0, 0, 0, 0.12)",
                    "borderRadius": "0.5rem",
                    "boxShadow": "0 1rem 2.5rem rgba(0, 0, 0, 0.25)",
                    "padding": "1rem",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "0.85rem",
                },
            ),
        ],
        id=ids.LANDMARK_REVIEW_PANE,
        style={
            "display": "none",
            "position": "fixed",
            "inset": 0,
            "zIndex": 11000,
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "rgba(248, 249, 250, 0.42)",
            "backdropFilter": "blur(1px)",
            "pointerEvents": "auto",
        },
    )

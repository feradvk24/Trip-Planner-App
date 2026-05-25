import dash_bootstrap_components as dbc
from dash import dcc, html

import ids
from i18n import t

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

import dash_bootstrap_components as dbc
from dash import html


def _stars(rating):
    if rating is None:
        return "No ratings yet"
    rounded = int(round(rating))
    return "★" * rounded + "☆" * (5 - rounded)


def build_empty_info():
    return html.Div(
        [
            html.Div(
                html.I(className="bi bi-info-circle", style={"fontSize": "2rem", "color": "#6c757d"}),
                style={"marginBottom": "0.5rem"},
            ),
            html.Div(
                "No information to display yet.",
                style={"color": "#6c757d", "fontSize": "0.95rem"},
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "textAlign": "center",
            "height": "100%",
        },
    )


def build_review_item(review):
    review_text = review.get("review_text")
    return html.Div(
        [
            html.Div(
                [
                    html.Span(_stars(review.get("rating")), style={"color": "#f2b01e", "fontSize": "0.9rem"}),
                    html.Small(review.get("created_at"), className="text-muted"),
                ],
                style={"display": "flex", "justifyContent": "space-between", "gap": "0.75rem"},
            ),
            html.Div(
                review.get("user_name") or review.get("username") or "User",
                style={"fontWeight": "600", "fontSize": "0.9rem", "marginTop": "0.25rem"},
            ),
            html.Div(
                review_text if review_text else "No written remarks.",
                className="text-muted" if not review_text else "",
                style={"fontSize": "0.9rem", "marginTop": "0.25rem", "lineHeight": "1.35"},
            ),
        ],
        style={
            "border": "1px solid #e9ecef",
            "borderRadius": "0.35rem",
            "padding": "0.75rem",
            "backgroundColor": "#ffffff",
        },
    )


def build_landmark_info(landmark, review_summary, reviews):
    average_rating = review_summary.get("average_rating")
    review_count = review_summary.get("review_count", 0)
    rating_text = f"{average_rating:.1f}" if average_rating is not None else "No score"

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Landmark",
                                style={"fontSize": "0.75rem", "color": "#6c757d", "textTransform": "uppercase"},
                            ),
                            html.H5(landmark.name, className="mb-1"),
                            html.Div(landmark.location, className="text-muted", style={"fontSize": "0.9rem"}),
                        ],
                    ),
                    html.A(
                        "Learn more",
                        href=landmark.link,
                        target="_blank",
                        className="btn btn-outline-primary btn-sm mt-3",
                    ) if landmark.link and landmark.link != "#" else None,
                ],
                style={"borderBottom": "1px solid #e9ecef", "paddingBottom": "1rem"},
            ),
            html.Div(
                [
                    html.Div(_stars(average_rating), style={"color": "#f2b01e", "fontSize": "1.4rem"}),
                    html.Div(
                        [
                            html.Span(rating_text, style={"fontWeight": "700"}),
                            html.Span(f" from {review_count} review{'s' if review_count != 1 else ''}", className="text-muted"),
                        ],
                        style={"fontSize": "0.95rem"},
                    ),
                ],
                style={"padding": "1rem 0", "borderBottom": "1px solid #e9ecef"},
            ),
            html.Div(
                [
                    html.H6("Reviews", className="mb-2"),
                    html.Div(
                        [build_review_item(review) for review in reviews]
                        if reviews else
                        [
                            dbc.Alert(
                                "No reviews for this landmark yet.",
                                color="light",
                                className="mb-0",
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "0.75rem"},
                    ),
                ],
                style={"paddingTop": "1rem"},
            ),
        ],
        style={"display": "flex", "flexDirection": "column"},
    )

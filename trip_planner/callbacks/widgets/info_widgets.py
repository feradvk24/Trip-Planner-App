import dash_bootstrap_components as dbc
from dash import html

import ids


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


def build_trip_info(trip, registry):
    destination_ids = [lid for lid in (trip.get("visit_order") or trip.get("landmark_ids") or []) if lid != -1]
    destinations = registry.get_landmarks(destination_ids)
    route_legs = trip.get("route_legs") or []
    distance_m = sum(leg.get("distance_m", 0) for leg in route_legs)
    distance_text = f"{distance_m / 1000:.1f} km" if distance_m >= 1000 else f"{int(round(distance_m))} m"
    owner = trip.get("owner_name") or trip.get("owner_username")
    completed_at = trip.get("completed_at")
    completion_rating = trip.get("completion_rating")
    completion_review_text = trip.get("completion_review_text")
    has_completion_review = completion_rating is not None or bool(completion_review_text)

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Shared trip" if trip.get("source") == "shared" else "Saved trip",
                        style={"fontSize": "0.75rem", "color": "#6c757d", "textTransform": "uppercase"},
                    ),
                    html.Div(f"By {owner}", className="text-muted", style={"fontSize": "0.9rem"}) if owner else None,
                    html.Div(trip.get("created_at"), className="text-muted", style={"fontSize": "0.85rem"}) if trip.get("created_at") else None,
                ],
                style={"borderBottom": "1px solid #e9ecef", "paddingBottom": "1rem"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Destinations", className="text-muted", style={"fontSize": "0.8rem"}),
                            html.Div(str(len(destination_ids)), style={"fontWeight": "700"}),
                        ],
                    ),
                    html.Div(
                        [
                            html.Div("Distance", className="text-muted", style={"fontSize": "0.8rem"}),
                            html.Div(distance_text if route_legs else "Unknown", style={"fontWeight": "700"}),
                        ],
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "0.75rem",
                    "padding": "1rem 0",
                    "borderBottom": "1px solid #e9ecef",
                },
            ),
            dbc.Alert(
                f"Completed: {completed_at}",
                color="success",
                className="mt-3 mb-0",
            ) if completed_at else None,
            html.Div(
                [
                    html.H6("Trip Review", className="mb-2"),
                    html.Div(_stars(completion_rating), style={"color": "#f2b01e", "fontSize": "1.1rem"}),
                    html.Div(
                        completion_review_text if completion_review_text else "No written remarks.",
                        className="text-muted" if not completion_review_text else "",
                        style={"fontSize": "0.9rem", "marginTop": "0.35rem", "lineHeight": "1.35"},
                    ),
                ],
                style={
                    "borderBottom": "1px solid #e9ecef",
                    "padding": "1rem 0",
                },
            ) if has_completion_review else None,
            html.Div(
                [
                    html.H6("Stops", className="mb-2"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(landmark.name, style={"fontWeight": "600", "fontSize": "0.9rem"}),
                                    html.Div(landmark.location, className="text-muted", style={"fontSize": "0.85rem"}),
                                ],
                                style={
                                    "border": "1px solid #e9ecef",
                                    "borderRadius": "0.35rem",
                                    "padding": "0.6rem 0.7rem",
                                    "backgroundColor": "#ffffff",
                                },
                            )
                            for landmark in destinations
                        ] or [dbc.Alert("No destinations to show.", color="light", className="mb-0")],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.5rem",
                            "flex": "1 1 auto",
                            "overflowY": "auto",
                            "overflowX": "hidden",
                            "minHeight": 0,
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "flex": "1 1 auto",
                    "flexDirection": "column",
                    "minHeight": 0,
                    "paddingTop": "1rem",
                },
            ),
            dbc.Button(
                "Select Trip",
                id=ids.SELECT_TRIP_BTN,
                color="info",
                className="w-100 mt-3",
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "height": "100%", "minHeight": 0},
    )

import dash_bootstrap_components as dbc
from dash import html

from trip_planner import ids
from trip_planner.i18n import t
from trip_planner.services.trip_route import TripRoute


def _stars(rating, lang="bg"):
    if rating is None:
        return t("reviews.no_ratings", lang=lang)
    rounded = int(round(rating))
    return "★" * rounded + "☆" * (5 - rounded)


def build_empty_info(lang="bg"):
    return html.Div(
        [
            html.Div(
                html.I(className="bi bi-info-circle", style={"fontSize": "2rem", "color": "#6c757d"}),
                style={"marginBottom": "0.5rem"},
            ),
            html.Div(
                t("info_sidebar.no_information", lang=lang),
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


def build_review_item(review, lang="bg"):
    review_text = review.get("review_text")
    children = [
        html.Div(
            [
                html.Span(_stars(review.get("rating"), lang=lang), style={"color": "#f2b01e", "fontSize": "0.9rem"}),
                html.Small(review.get("created_at"), className="text-muted"),
            ],
            style={"display": "flex", "justifyContent": "space-between", "gap": "0.75rem"},
        ),
        html.Div(
            review.get("user_name") or review.get("username") or t("generic.user", lang=lang),
            style={"fontWeight": "600", "fontSize": "0.9rem", "marginTop": "0.25rem"},
        ),
    ]
    if review_text:
        children.append(
            html.Div(
                review_text,
                style={"fontSize": "0.9rem", "marginTop": "0.25rem", "lineHeight": "1.35"},
            )
        )
    return html.Div(
        children,
        style={
            "border": "1px solid #e9ecef",
            "borderRadius": "0.35rem",
            "padding": "0.75rem",
            "backgroundColor": "#ffffff",
        },
    )


def build_landmark_info(landmark, review_summary, reviews, lang="bg"):
    average_rating = review_summary.get("average_rating")
    review_count = review_summary.get("review_count", 0)
    rating_text = f"{average_rating:.1f}" if average_rating is not None else t("reviews.no_score", lang=lang)

    return html.Div(
        [
            html.Div(
                [
                    html.Div(_stars(average_rating, lang=lang), style={"color": "#f2b01e", "fontSize": "1.4rem"}),
                    html.Div(
                        [
                            html.Span(rating_text, style={"fontWeight": "700"}),
                            html.Span(f" {t('reviews.from_count', lang=lang).format(count=review_count)}", className="text-muted"),
                        ],
                        style={"fontSize": "0.95rem"},
                    ),
                ],
                style={"padding": "1rem 0", "borderBottom": "1px solid #e9ecef"},
            ),
            html.Div(
                [
                    html.H6(t("reviews.title", lang=lang), className="mb-2"),
                    html.Div(
                        [build_review_item(review, lang=lang) for review in reviews]
                        if reviews else
                        [
                            dbc.Alert(
                                t("reviews.none_for_landmark", lang=lang),
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


def build_trip_info(trip, registry, lang="bg"):
    route_legs = trip.get("route_legs") or []
    destination_ids = TripRoute.handle_trip_store(trip)["destination_ids"]
    destinations = registry.landmarks_by_ids(destination_ids)
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
                        t("info_sidebar.shared_trip", lang=lang) if trip.get("source") == "shared" else t("info_sidebar.saved_trip", lang=lang),
                        style={"fontSize": "0.75rem", "color": "#6c757d", "textTransform": "uppercase"},
                    ),
                    html.Div(f"{t('info_sidebar.by', lang=lang)} {owner}", className="text-muted", style={"fontSize": "0.9rem"}) if owner else None,
                    html.Div(trip.get("created_at"), className="text-muted", style={"fontSize": "0.85rem"}) if trip.get("created_at") else None,
                ],
                style={"borderBottom": "1px solid #e9ecef", "paddingBottom": "1rem"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(t("info_sidebar.destinations", lang=lang), className="text-muted", style={"fontSize": "0.8rem"}),
                            html.Div(str(len(destination_ids)), style={"fontWeight": "700"}),
                        ],
                    ),
                    html.Div(
                        [
                            html.Div(t("info_sidebar.distance", lang=lang), className="text-muted", style={"fontSize": "0.8rem"}),
                            html.Div(distance_text, style={"fontWeight": "700"}),
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
                f"{t('trip_list.completed', lang=lang)}: {completed_at}",
                color="success",
                className="mt-3 mb-0",
            ) if completed_at else None,
            html.Div(
                [
                    html.H6(t("info_sidebar.trip_review", lang=lang), className="mb-2"),
                    html.Div(_stars(completion_rating, lang=lang), style={"color": "#f2b01e", "fontSize": "1.1rem"}),
                    html.Div(
                        completion_review_text,
                        style={"fontSize": "0.9rem", "marginTop": "0.35rem", "lineHeight": "1.35"},
                    ) if completion_review_text else None,
                ],
                style={
                    "borderBottom": "1px solid #e9ecef",
                    "padding": "1rem 0",
                },
            ) if has_completion_review else None,
            html.Div(
                [
                    html.H6(t("info_sidebar.stops", lang=lang), className="mb-2"),
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
                        ] or [dbc.Alert(t("info_sidebar.no_destinations", lang=lang), color="light", className="mb-0")],
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
                t("info_sidebar.select_trip", lang=lang),
                id=ids.SELECT_TRIP_BTN,
                color="info",
                className="w-100 mt-3",
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "height": "100%", "minHeight": 0},
    )

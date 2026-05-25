import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import app_context
import ids
from backend.crud import get_user_landmark_visit_history, get_user_monthly_landmark_visit_counts, total_landmark_visits_for_user
from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, t
from layout.sidebar import create_user_menu


dash.register_page(__name__, path_template="/<lang>/statistics", name="Statistics", order=2)


MAX_VISIT_HISTORY_ITEMS = 100
MONTHLY_VISIT_CHART_MONTHS = 6


def build_visit_history_items(registry, visits, limit=MAX_VISIT_HISTORY_ITEMS, lang="bg"):
    visits = (visits or [])[:limit]
    if not visits:
        return [
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.Div(t("statistics.no_visited_landmarks", lang=lang), className="fw-semibold"),
                        html.Div(
                            t("statistics.visited_landmarks_will_appear", lang=lang),
                            className="text-muted small",
                        ),
                    ],
                    className="py-2",
                )
            )
        ]

    items = []
    for visit in visits:
        landmark = registry.get_landmark(visit.get("landmark_id"))
        landmark_name = landmark.name if landmark else f"Landmark {visit.get('landmark_id')}"
        landmark_location = landmark.location if landmark else ""
        items.append(
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(landmark_name, className="fw-semibold"),
                                html.Small(visit.get("visited_at", ""), className="text-muted"),
                            ],
                            className="d-flex justify-content-between gap-3",
                        ),
                        html.Div(landmark_location, className="text-muted small"),
                        html.Div(
                            f"Trip: {visit.get('trip_name', 'Unknown trip')}",
                            className="small",
                        ),
                    ],
                    className="d-flex flex-column gap-1",
                )
            )
        )
    return items


def build_monthly_visit_figure(monthly_visits):
    months = [row["month"] for row in monthly_visits]
    counts = [row["count"] for row in monthly_visits]
    return {
        "data": [
            {
                "type": "bar",
                "x": months,
                "y": counts,
                "marker": {"color": "#0d6efd"},
                "hovertemplate": "%{x}<br>%{y} visits<extra></extra>",
            }
        ],
        "layout": {
            "height": 260,
            "autosize": True,
            "margin": {"l": 38, "r": 8, "t": 12, "b": 42},
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "xaxis": {"title": None, "fixedrange": True},
            "yaxis": {
                "title": "Visits",
                "fixedrange": True,
                "rangemode": "tozero",
                "dtick": 1,
            },
            "showlegend": False,
        },
    }


def build_total_visits(total_visits, lang="bg"):
    return html.Div(
        [
            html.Div(t("statistics.total_landmark_visits", lang=lang), className="text-muted small", style={"textAlign": "center"}),
            html.Div(
                f"{total_visits}",
                className="fs-4 fw-semibold",
                style={"width": "100%", "textAlign": "center"},
            ),
        ],
        className="d-flex flex-column align-items-start gap-1 py-3 px-4 border rounded",
        style={"width": "10rem", "backgroundColor": "white"},
    )


def layout(lang="bg", **kwargs):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    visits = (
        get_user_landmark_visit_history(current_user.id, limit=MAX_VISIT_HISTORY_ITEMS)
        if current_user.is_authenticated else
        []
    )
    monthly_visits = (
        get_user_monthly_landmark_visit_counts(current_user.id, months=MONTHLY_VISIT_CHART_MONTHS)
        if current_user.is_authenticated else
        []
    )
    total_visits = total_landmark_visits_for_user(current_user.id) if current_user.is_authenticated else 0

    return html.Div(
        [
            create_user_menu(fix_to_right=True, lang=lang),
            dbc.Container(
                [
                    html.Div(
                        [
                            dcc.Link(
                                [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                                href=f"/{lang}",
                                className="btn btn-outline-secondary btn-sm mb-3",
                            ),
                            html.H2(t("statistics.title", lang=lang), className="mb-2"),
                            html.P(
                                t("statistics.subtitle", lang=lang),
                                className="text-muted mb-0",
                            ),
                        ],
                        style={"flex": "0 0 auto"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    build_total_visits(total_visits, lang=lang),
                                    html.H4(t("statistics.landmark_visits", lang=lang), className="mt-4 mb-3"),
                                    dcc.Graph(
                                        figure=build_monthly_visit_figure(monthly_visits),
                                        config={"displayModeBar": False, "responsive": True},
                                        responsive=True,
                                        style={"width": "100%", "maxWidth": "100%"},
                                    ),
                                ],
                                style={
                                    "flex": "1 1 34rem",
                                    "minWidth": "min(100%, 20rem)",
                                    "maxWidth": "100%",
                                },
                            ),
                            html.Div(
                                [
                                    html.H4(t("statistics.visit_history", lang=lang), className="mb-3"),
                                    dbc.ListGroup(
                                        id=ids.VISIT_HISTORY_LIST,
                                        children=build_visit_history_items(app_context.REGISTRY, visits),
                                        flush=True,
                                        style={
                                            "flex": "1 1 auto",
                                            "minHeight": 0,
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                style={
                                    "flex": "1 1 26rem",
                                    "minWidth": "min(100%, 20rem)",
                                    "maxWidth": "100%",
                                    "maxHeight": "100%",
                                    "minHeight": 0,
                                    "display": "flex",
                                    "flexDirection": "column",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "gap": "2rem",
                            "alignItems": "flex-start",
                            "flexWrap": "wrap",
                            "flex": "1 1 auto",
                            "minHeight": 0,
                            "overflow": "auto",
                        },
                    ),
                ],
                fluid=True,
                className="py-4",
                style={
                    "minHeight": "100vh",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "1.5rem",
                    "overflow": "auto",
                },
            ),
        ],
        id=ids.PAGE_CONTENT,
        style={"minHeight": "100vh", "overflow": "auto"},
    )

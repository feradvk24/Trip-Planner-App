import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import app_context
import ids
from backend.crud import get_user_landmark_visit_history
from layout.sidebar import create_user_menu


dash.register_page(__name__, path="/statistics", name="Statistics")


MAX_VISIT_HISTORY_ITEMS = 100


def build_visit_history_items(registry, visits, limit=MAX_VISIT_HISTORY_ITEMS):
    visits = (visits or [])[:limit]
    if not visits:
        return [
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.Div("No visited landmarks yet.", className="fw-semibold"),
                        html.Div(
                            "Visited landmarks will appear here after you progress through a trip.",
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


def layout(**kwargs):
    visits = (
        get_user_landmark_visit_history(current_user.id, limit=MAX_VISIT_HISTORY_ITEMS)
        if current_user.is_authenticated else
        []
    )
    return html.Div(
        [
            create_user_menu(),
            dbc.Container(
                [
                    dcc.Link(
                        [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                        href="/",
                        className="btn btn-outline-secondary btn-sm mb-3",
                    ),
                    html.H2("Statistics", className="mb-2"),
                    html.P(
                        "Your trip statistics will live here.",
                        className="text-muted",
                    ),
                    html.H4("Visit History", className="mt-4 mb-3"),
                    dbc.ListGroup(
                        id=ids.VISIT_HISTORY_LIST,
                        children=build_visit_history_items(app_context.REGISTRY, visits),
                        flush=True,
                        style={
                            "maxWidth": "52rem",
                            "maxHeight": "calc(100vh - 13rem)",
                            "overflowY": "auto",
                        },
                    ),
                ],
                fluid=True,
                className="py-4",
            ),
        ],
        id=ids.PAGE_CONTENT,
    )

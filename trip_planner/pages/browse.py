import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

import ids
from layout.sidebar import create_user_menu


dash.register_page(__name__, path="/browse", name="Browse")


def layout(**kwargs):
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
                    html.H2("Browse Trips", className="mb-2"),
                    html.P(
                        "This page will replace the Browse overlay.",
                        className="text-muted",
                    ),
                    dbc.Alert(
                        "Next step: move saved trips, shared trips, visit history, and featured landmarks here.",
                        color="info",
                    ),
                ],
                fluid=True,
                className="py-4",
            ),
        ],
        id=ids.PAGE_CONTENT,
    )

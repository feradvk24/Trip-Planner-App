from dash import html

import ids
from styles import INFO_SIDEBAR_STYLE


def create_info_sidebar():
    return html.Aside(
        [
            html.Div(
                [
                    html.Div(
                        "Details",
                        id=ids.INFO_SIDEBAR_TITLE,
                        style={"fontSize": "1.6rem", "fontWeight": "700", "lineHeight": "1.15"},
                    ),
                    html.Div(
                        "No selection",
                        id=ids.INFO_SIDEBAR_SUBTITLE,
                        style={"fontSize": "0.85rem", "color": "#6c757d"},
                    ),
                ],
                style={
                    "borderBottom": "1px solid #e9ecef",
                    "paddingBottom": "0.75rem",
                    "marginBottom": "1rem",
                },
            ),
            html.Div(
                [
                    html.Div(
                        html.I(className="bi bi-info-circle", style={"fontSize": "2rem", "color": "#6c757d"}),
                        style={"marginBottom": "0.5rem"},
                    ),
                    html.Div(
                        "Details will appear here.",
                        style={"color": "#6c757d", "fontSize": "0.95rem"},
                    ),
                ],
                id=ids.INFO_SIDEBAR_BODY,
                style={
                    "flex": "1 1 auto",
                    "minHeight": 0,
                    "overflowY": "auto",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "textAlign": "center",
                },
            ),
        ],
        id=ids.INFO_SIDEBAR,
        style=INFO_SIDEBAR_STYLE,
    )

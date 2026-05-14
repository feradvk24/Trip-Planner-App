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
                    html.Div(
                        id=ids.INFO_SIDEBAR_ACTIONS,
                        style={"marginTop": "0.75rem"},
                    ),
                    html.A(
                        [
                            html.Img(
                                id=ids.INFO_SIDEBAR_IMAGE,
                                src=None,
                                alt="",
                                hidden=True,
                                style={
                                    "width": "100%",
                                    "height": "10rem",
                                    "objectFit": "cover",
                                    "border": "1px solid #e9ecef",
                                    "borderRadius": "0.35rem",
                                    "backgroundColor": "#f8f9fa",
                                    "display": "block",
                                },
                            ),
                            html.Div(
                                id=ids.INFO_SIDEBAR_IMAGE_META,
                                className="info-sidebar-image-meta",
                            ),
                        ],
                        id=ids.INFO_SIDEBAR_IMAGE_LINK,
                        className="info-sidebar-image-link",
                        href=None,
                        target="_blank",
                        rel="noopener noreferrer",
                        title="",
                        hidden=True,
                        style={
                            "display": "block",
                            "marginTop": "0.75rem",
                            "cursor": "pointer",
                        },
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

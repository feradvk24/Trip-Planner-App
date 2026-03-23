pin_icon = {
    "iconUrl": "/assets/marker-pin.png",
    "iconSize": [30, 30],      # size of the icon
    # "iconAnchor": [15, 40],    # point of the icon which corresponds to marker location
}

checkbox_icon = {
    "iconUrl": "/assets/marker-check.png",
    "iconSize": [30, 30],
    # "iconAnchor": [12, 12],
}

import base64 as _b64


def _svg_to_icon(svg: str, size: int) -> dict:
    encoded = _b64.b64encode(svg.encode()).decode()
    half = size // 2
    return {
        "iconUrl": f"data:image/svg+xml;base64,{encoded}",
        "iconSize": [size, size],
        "iconAnchor": [half, half],
    }


def number_icon(n: int) -> dict:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28">'
        f'<circle cx="14" cy="14" r="13" fill="#1a6fcf" stroke="white" stroke-width="2"/>'
        f'<text x="14" y="19" text-anchor="middle" font-size="13" font-weight="bold" '
        f'font-family="Arial,sans-serif" fill="white">{n}</text>'
        f'</svg>'
    )
    return _svg_to_icon(svg, 28)


def location_dot_icon() -> dict:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22">'
        '<circle cx="11" cy="11" r="9" fill="#1a6fcf" stroke="white" stroke-width="3"/>'
        '</svg>'
    )
    return _svg_to_icon(svg, 22)

# Sidebar styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "borderRight": "1px solid #dee2e6",
    "display": "flex",
    "flexDirection": "column",
    "overflow": "hidden",
}

# Main content styles
CONTENT_STYLE = {
    "marginLeft": "18rem",
    "height": "100vh",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
}
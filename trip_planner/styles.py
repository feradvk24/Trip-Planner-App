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


def grayed_number_icon(n: int) -> dict:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28">'
        f'<circle cx="14" cy="14" r="13" fill="#9e9e9e" stroke="white" stroke-width="2"/>'
        f'<text x="14" y="19" text-anchor="middle" font-size="13" font-weight="bold" '
        f'font-family="Arial,sans-serif" fill="white">{n}</text>'
        f'</svg>'
    )
    return _svg_to_icon(svg, 28)


def current_point_icon(n: int) -> dict:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">'
        f'<circle cx="18" cy="18" r="16" fill="#e53935" stroke="white" stroke-width="2.5"/>'
        f'<text x="18" y="24" text-anchor="middle" font-size="14" font-weight="bold" '
        f'font-family="Arial,sans-serif" fill="white">{n}</text>'
        f'</svg>'
    )
    return _svg_to_icon(svg, 36)


def house_icon() -> dict:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
        '<circle cx="16" cy="16" r="15" fill="#198754" stroke="white" stroke-width="2"/>'
        '<path d="M8 16.4 16 9l8 7.4" fill="none" stroke="white" stroke-width="2.4" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M10.5 15.2V23h11V15.2" fill="none" stroke="white" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M14 23v-5h4v5" fill="none" stroke="white" stroke-width="2.1" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    return _svg_to_icon(svg, 32)


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
    "zIndex": 1040,
}

INFO_SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "right": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "1.25rem",
    "backgroundColor": "#ffffff",
    "borderLeft": "1px solid #dee2e6",
    "display": "flex",
    "flexDirection": "column",
    "overflow": "hidden",
    "zIndex": 1030,
}

# Main content styles
CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "20rem",
    "height": "100vh",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
}

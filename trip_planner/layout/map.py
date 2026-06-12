from dash import html
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from trip_planner import ids


def create_map(markers, initial_viewport=None):
    initial_center = initial_viewport["center"] if initial_viewport else [42.7, 25.0]
    initial_zoom = initial_viewport["zoom"] if initial_viewport else 7.4
    viewport_props = {"viewport": initial_viewport} if initial_viewport else {}

    return dl.Map(
        children=[
            dl.TileLayer(),
            dl.Polygon(
                positions=[
                    [[90, -180], [90, 180], [-90, 180], [-90, -180]],
                    [[41.0, 22.0], [41.0, 28.6], [44.3, 28.6], [44.3, 22.0]],
                ],
                color="black",
                fillColor="black",
                fillOpacity=0.6,
                weight=0,
                interactive=False,
            ),
            dl.LayerGroup(id=ids.PLANNED_TRIP_POLYLINE_LAYER),
            dl.Pane(
                name=ids.TRIP_PASSED_ROUTE_PANE,
                style={"zIndex": 541},
            ),
            dl.Pane(
                name=ids.TRIP_REMAINING_ROUTE_PANE,
                style={"zIndex": 542},
            ),
            dl.Pane(
                name=ids.TRIP_CURRENT_ROUTE_PANE,
                style={"zIndex": 543},
            ),
            dl.Pane(
                dl.LayerGroup(id=ids.LOADED_TRIP_POLYLINE_LAYER),
                name="trip-route-pane",
                style={"zIndex": 540},
            ),
            dl.Pane(
                dl.LayerGroup(id=ids.LOADED_TRIP_OVERVIEW_POLYLINE_LAYER),
                name="trip-overview-route-pane",
                style={"zIndex": 560},
            ),
            dl.LayerGroup(id=ids.USER_LOCATION_LAYER),
            dl.LayerGroup(id=ids.ALL_MARKERS_LAYER, children=markers),
            dl.LayerGroup(id=ids.SEARCH_POPUP_LAYER, children=[]),
            dl.LayerGroup(id=ids.PLANNED_TRIP_MARKERS_LAYER, children=[]),
            dl.LayerGroup(id=ids.LOADED_TRIP_MARKERS_LAYER, children=[]),
            html.Div(
                id=ids.ROUTE_STATS_PANEL,
                style={
                    "display": "none",
                    "position": "absolute",
                    "bottom": "1.5rem",
                    "left": "1rem",
                    "zIndex": 1000,
                    "background": "rgba(255,255,255,0.92)",
                    "borderRadius": "0.375rem",
                    "padding": "0.5rem 0.75rem",
                    "boxShadow": "0 1px 5px rgba(0,0,0,0.3)",
                    "fontSize": "0.85rem",
                    "lineHeight": "1.6",
                    "pointerEvents": "none",
                },
            ),
            html.Div(
                dbc.Spinner(color="primary", type="border"),
                id=ids.ROUTE_LOADING_OVERLAY,
                style={
                    "display": "none",
                    "position": "absolute",
                    "inset": 0,
                    "zIndex": 2000,
                    "alignItems": "center",
                    "justifyContent": "center",
                    "background": "rgba(255,255,255,0.38)",
                    "pointerEvents": "none",
                },
            ),
        ],
        center=initial_center,
        zoom=initial_zoom,
        minZoom=7.4,
        maxBounds=[[41.0, 22.0], [44.3, 28.6]],
        maxBoundsViscosity=1.0,
        zoomSnap=1,
        zoomDelta=0.66,
        wheelPxPerZoomLevel=200,
        zoomAnimation=True,
        style={"width": "100%", "height": "100%"},
        id=ids.MAP,
        **viewport_props,
    )

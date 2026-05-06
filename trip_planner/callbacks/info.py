from dash import ALL, Input, Output, ctx
from dash.exceptions import PreventUpdate

import ids
from backend.crud import get_landmark_review_summary, get_landmark_reviews
from callbacks.widgets.info_widgets import build_empty_info, build_landmark_info


def register_info_callbacks(app, registry):
    @app.callback(
        Output(ids.ACTIVE_INFO_STORE, "data"),
        Input({"type": "marker", "index": ALL}, "n_clicks"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.MODE_STORE, "data"),
        prevent_initial_call=True,
    )
    def select_info_sidebar_mode(marker_clicks, trip_data, mode):
        triggered_id = ctx.triggered_id
        triggered_value = ctx.triggered[0].get("value") if ctx.triggered else None

        if not triggered_id:
            raise PreventUpdate

        if triggered_id in (ids.ACTIVE_TRIP_STORE, ids.MODE_STORE):
            if mode != "trip":
                raise PreventUpdate
            if not trip_data:
                raise PreventUpdate
            return {
                "type": "trip",
                "content": trip_data.get("id"),
            }
        if isinstance(triggered_id, dict) and triggered_id.get("type") == "marker":
            if not triggered_value:
                raise PreventUpdate
            return {
                "type": "landmark",
                "content": triggered_id["index"],
            }

        raise PreventUpdate

    @app.callback(
        Output(ids.INFO_SIDEBAR_TITLE, "children"),
        Output(ids.INFO_SIDEBAR_SUBTITLE, "children"),
        Output(ids.INFO_SIDEBAR_BODY, "children"),
        Output(ids.INFO_SIDEBAR_BODY, "style"),
        Input(ids.ACTIVE_INFO_STORE, "data"),
    )
    def render_info_sidebar(active_info):
        base_style = {
            "flex": "1 1 auto",
            "minHeight": 0,
            "overflowY": "auto",
        }

        if not active_info:
            return "Details", "No selection", build_empty_info(), {
                **base_style,
                "display": "block",
            }

        if active_info.get("type") == "trip":
            # For now, just show a placeholder for trip info
            return "Trip Details", "Feature coming soon", build_empty_info(), {
                **base_style,
                "display": "block",
            }
        elif active_info.get("type") == "landmark":

            landmark = registry.get_landmark(active_info.get("content"))
            if not landmark:
                return "Details", "No selection", build_empty_info(), {
                    **base_style,
                    "display": "block",
                }
            review_summary = get_landmark_review_summary(landmark.id)
            reviews = get_landmark_reviews(landmark.id)
            return "Landmark", landmark.name, build_landmark_info(landmark, review_summary, reviews), {
                **base_style,
                "display": "block",
            }
        else:
            raise PreventUpdate

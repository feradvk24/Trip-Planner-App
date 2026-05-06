from dash import ALL, Input, Output, ctx
from dash.exceptions import PreventUpdate

import ids
from backend.crud import get_landmark_review_summary, get_landmark_reviews
from callbacks.widgets.info_widgets import build_empty_info, build_landmark_info


def register_info_callbacks(app, registry):
    @app.callback(
        Output(ids.ACTIVE_INFO_STORE, "data"),
        Input({"type": "marker", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def select_landmark_info(marker_clicks):
        if not ctx.triggered_id or not any(n for n in marker_clicks if n):
            raise PreventUpdate
        return {
            "type": "landmark",
            "landmark_id": ctx.triggered_id["index"],
        }

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

        if active_info.get("type") != "landmark":
            return "Details", "No selection", build_empty_info(), {
                **base_style,
                "display": "block",
            }

        landmark = registry.get_landmark(active_info.get("landmark_id"))
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

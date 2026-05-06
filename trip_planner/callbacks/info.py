from dash import ALL, Input, Output, ctx
from dash.exceptions import PreventUpdate

import ids
from backend.crud import get_landmark_review_summary, get_landmark_reviews
from callbacks.utils.trip_state import next_action_stop_index
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
            stop_ids = trip_data.get("visit_order") or []
            next_stop_index = next_action_stop_index(trip_data)
            if next_stop_index is None or next_stop_index >= len(stop_ids):
                return {
                    "type": "trip",
                    "content": None,
                }
            return {
                "type": "trip",
                "content": stop_ids[next_stop_index],
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
            landmark = registry.get_landmark(active_info.get("content"))
            if not landmark:
                return "Trip Details", "No next stop", build_empty_info(), {
                    **base_style,
                    "display": "block",
                }
            review_summary = get_landmark_review_summary(landmark.id)
            reviews = get_landmark_reviews(landmark.id)
            return "Trip Details", landmark.name, build_landmark_info(landmark, review_summary, reviews), {
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

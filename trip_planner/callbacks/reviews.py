from dash import ALL, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from flask_login import current_user

import ids
from backend.crud import create_landmark_review, create_trip_completion
from callbacks.utils.get_language import get_language_from_url
from callbacks.widgets.review_widgets import landmark_review_pane_style, landmark_review_star_buttons
from i18n import t


def _next_review_state_or_close(review_state):
    next_review_state = (review_state or {}).get("next_review_state")
    if next_review_state:
        return next_review_state
    return {**(review_state or {}), "is_open": False}


def register_review_callbacks(app):
    @app.callback(
        Output(ids.LANDMARK_REVIEW_STATE_STORE, "data", allow_duplicate=True),
        Output(ids.LANDMARK_REVIEW_TEXT, "value", allow_duplicate=True),
        Input(ids.LANDMARK_REVIEW_CLOSE_BTN, "n_clicks"),
        Input(ids.LANDMARK_REVIEW_SKIP_BTN, "n_clicks"),
        State(ids.LANDMARK_REVIEW_STATE_STORE, "data"),
        prevent_initial_call=True,
    )
    def close_landmark_review_pane(close_clicks, skip_clicks, review_state):
        if not close_clicks and not skip_clicks:
            raise PreventUpdate
        return _next_review_state_or_close(review_state), ""

    @app.callback(
        Output(ids.LANDMARK_REVIEW_STATE_STORE, "data", allow_duplicate=True),
        Input({"type": "landmark-review-star-btn", "index": ALL}, "n_clicks"),
        State(ids.LANDMARK_REVIEW_STATE_STORE, "data"),
        prevent_initial_call=True,
    )
    def select_landmark_review_rating(star_clicks, review_state):
        if not ctx.triggered_id or not any(n for n in star_clicks if n):
            raise PreventUpdate
        return {**(review_state or {}), "rating": ctx.triggered_id["index"]}

    @app.callback(
        Output(ids.LANDMARK_REVIEW_PANE, "style"),
        Output(ids.LANDMARK_REVIEW_EYEBROW, "children"),
        Output(ids.LANDMARK_REVIEW_EYEBROW, "style"),
        Output(ids.LANDMARK_REVIEW_TITLE, "children"),
        Output(ids.LANDMARK_REVIEW_LOCATION, "children"),
        Output(ids.LANDMARK_REVIEW_STAR_ROW, "children"),
        Output(ids.LANDMARK_REVIEW_TEXT, "placeholder"),
        Output(ids.LANDMARK_REVIEW_SHARE_TRIP_BTN, "style"),
        Input(ids.LANDMARK_REVIEW_STATE_STORE, "data"),
        State("url", "href"),
    )
    def render_landmark_review_pane(review_state, href):
        lang = get_language_from_url(href)
        review_state = review_state or {}
        display = "flex" if review_state.get("is_open") else "none"
        is_trip_completion_review = review_state.get("review_type") == "trip_completion"
        eyebrow_style = {"fontSize": "0.8rem", "color": "#6C757D"}
        if is_trip_completion_review:
            eyebrow_style = {**eyebrow_style, "display": "none"}
        return (
            landmark_review_pane_style(display),
            "" if is_trip_completion_review else t("landmark_review.leave_review", lang=lang),
            eyebrow_style,
            t("trip_status.trip_complete", lang=lang) if is_trip_completion_review else review_state.get("title", ""),
            (
                t("landmark_review.ready_for_adventure", lang=lang)
                if is_trip_completion_review else
                review_state.get("location", "")
            ),
            landmark_review_star_buttons(review_state.get("rating"), lang=lang),
            (
                t("landmark_review.trip_placeholder", lang=lang)
                if is_trip_completion_review else
                t("landmark_review.placeholder", lang=lang)
            ),
            {"display": "inline-block"} if is_trip_completion_review else {"display": "none"},
        )

    @app.callback(
        Output(ids.LANDMARK_REVIEW_STATE_STORE, "data", allow_duplicate=True),
        Output(ids.LANDMARK_REVIEW_ALERT, "children"),
        Output(ids.LANDMARK_REVIEW_ALERT, "color"),
        Output(ids.LANDMARK_REVIEW_ALERT, "is_open", allow_duplicate=True),
        Output(ids.LANDMARK_REVIEW_TEXT, "value", allow_duplicate=True),
        Input(ids.LANDMARK_REVIEW_SUBMIT_BTN, "n_clicks"),
        State(ids.LANDMARK_REVIEW_STATE_STORE, "data"),
        State(ids.LANDMARK_REVIEW_TEXT, "value"),
        State(ids.ACTIVE_TRIP_STORE, "data"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def submit_landmark_review(n_clicks, review_state, review_text, active_trip, href):
        if not n_clicks:
            raise PreventUpdate
        lang = get_language_from_url(href)
        review_state = review_state or {}
        is_trip_completion_review = review_state.get("review_type") == "trip_completion"
        landmark_id = review_state.get("landmark_id")
        rating = review_state.get("rating")
        if not active_trip or not active_trip.get("trip_id") or (not is_trip_completion_review and not landmark_id):
            return (
                {**review_state, "is_open": True},
                t("landmark_review.missing_target", lang=lang),
                "danger",
                True,
                review_text,
            )
        if rating is None:
            return (
                {**review_state, "is_open": True},
                t("landmark_review.choose_rating", lang=lang),
                "warning",
                True,
                review_text,
            )

        try:
            if is_trip_completion_review:
                create_trip_completion(
                    username=current_user.id,
                    trip_id=active_trip["trip_id"],
                    rating=int(rating),
                    review_text=review_text,
                )
            else:
                create_landmark_review(
                    username=current_user.id,
                    trip_id=active_trip["trip_id"],
                    landmark_id=int(landmark_id),
                    rating=int(rating),
                    review_text=review_text,
                )
        except Exception as e:
            return (
                {**review_state, "is_open": True},
                f"{t('landmark_review.save_failed', lang=lang)}: {e}",
                "danger",
                True,
                review_text,
            )

        return _next_review_state_or_close(review_state), "", "success", False, ""

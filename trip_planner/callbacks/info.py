from dash import ALL, Input, Output, ctx, html
from dash.exceptions import PreventUpdate

import ids
from backend.crud import get_landmark_image, get_landmark_review_summary, get_landmark_reviews
from callbacks.utils.trip_state import next_action_stop_index
from callbacks.widgets.info_widgets import build_empty_info, build_landmark_info, build_trip_info


def _image_label(image):
    if not image:
        return ""
    return image.get("commons_file") or "Landmark image"


def _image_tooltip(image):
    if not image:
        return ""

    parts = [_image_label(image)]
    author = image.get("author")
    if author:
        parts.append(f"Author: {author}")
    return "\n".join(part for part in parts if part)


def _image_meta(image):
    if not image:
        return []

    children = [
        html.Div(_image_label(image), className="info-sidebar-image-label"),
    ]
    author = image.get("author")
    if author:
        children.append(html.Div(f"Author: {author}", className="info-sidebar-image-author"))
    return children


def _learn_more_action(landmark):
    if not landmark or not landmark.link or landmark.link == "#":
        return []
    return html.A(
        "Learn more",
        href=landmark.link,
        target="_blank",
        rel="noopener noreferrer",
        className="btn btn-outline-primary btn-sm",
    )


def register_info_callbacks(app, registry):
    @app.callback(
        Output(ids.ACTIVE_INFO_STORE, "data"),
        Input({"type": "marker", "index": ALL}, "n_clicks"),
        Input({"type": "route-marker", "index": ALL, "landmark_id": ALL}, "n_clicks"),
        Input(ids.ACTIVE_TRIP_STORE, "data"),
        Input(ids.MODE_STORE, "data"),
        prevent_initial_call=True,
    )
    def select_info_sidebar_mode(marker_clicks, route_marker_clicks, trip_data, mode):
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
            if next_stop_index is None:
                return {
                    "type": "trip",
                    "content": None,
                }
            if next_stop_index >= len(stop_ids):
                raise PreventUpdate
            return {
                "type": "trip",
                "content": stop_ids[next_stop_index],
            }
        if isinstance(triggered_id, dict) and triggered_id.get("type") in ("marker", "route-marker"):
            if not triggered_value:
                raise PreventUpdate
            return {
                "type": "landmark",
                "content": triggered_id.get("landmark_id", triggered_id["index"]),
            }

        raise PreventUpdate

    @app.callback(
        Output(ids.INFO_SIDEBAR_TITLE, "children"),
        Output(ids.INFO_SIDEBAR_SUBTITLE, "children"),
        Output(ids.INFO_SIDEBAR_ACTIONS, "children"),
        Output(ids.INFO_SIDEBAR_IMAGE_LINK, "hidden"),
        Output(ids.INFO_SIDEBAR_IMAGE_LINK, "href"),
        Output(ids.INFO_SIDEBAR_IMAGE_LINK, "title"),
        Output(ids.INFO_SIDEBAR_IMAGE, "hidden"),
        Output(ids.INFO_SIDEBAR_IMAGE, "src"),
        Output(ids.INFO_SIDEBAR_IMAGE, "alt"),
        Output(ids.INFO_SIDEBAR_IMAGE_META, "children"),
        Output(ids.INFO_SIDEBAR_BODY, "children"),
        Output(ids.INFO_SIDEBAR_BODY, "style"),
        Input(ids.ACTIVE_INFO_STORE, "data"),
        Input(ids.SELECTED_TRIP_STORE, "data"),
        Input(ids.BROWSE_OVERLAY_STORE, "data"),
        Input(ids.MODE_STORE, "data"),
    )
    def render_info_sidebar(active_info, selected_trip, browse_open, mode):
        base_style = {
            "flex": "1 1 auto",
            "minHeight": 0,
            "overflowY": "auto",
        }
        hide_landmark_image = mode not in ("explore", "trip")

        if browse_open:
            if selected_trip:
                trip_name = selected_trip.get("name") or "Selected trip"
                return trip_name, "Shared trip" if selected_trip.get("source") == "shared" else "Saved trip", [], True, None, "", True, None, "", [], build_trip_info(selected_trip, registry), {
                    **base_style,
                    "display": "block",
                    "overflow": "hidden",
                }
            return "Browse Trips", "No trip selected", [], True, None, "", True, None, "", [], build_empty_info(), {
                **base_style,
                "display": "block",
            }

        if not active_info:
            return "Details", "No selection", [], True, None, "", True, None, "", [], build_empty_info(), {
                **base_style,
                "display": "block",
            }

        if active_info.get("type") in ("trip", "landmark"):
            landmark = registry.get_landmark(active_info.get("content"))
            if not landmark:
                title = "Trip Complete" if active_info.get("type") == "trip" else "Details"
                subtitle = "No next stop" if active_info.get("type") == "trip" else "No selection"
                return title, subtitle, [], True, None, "", True, None, "", [], build_empty_info(), {
                    **base_style,
                    "display": "block",
                }
            image = get_landmark_image(landmark.id)
            image_src = image.get("src_link") if image else None
            image_hidden = hide_landmark_image or not image_src
            image_source_url = image.get("image_source_url") or image_src if image else None
            image_alt = _image_label(image)
            image_title = _image_tooltip(image)
            review_summary = get_landmark_review_summary(landmark.id)
            reviews = get_landmark_reviews(landmark.id)
            return landmark.name, landmark.location, _learn_more_action(landmark), image_hidden, image_source_url, image_title, image_hidden, image_src, image_alt, _image_meta(image), build_landmark_info(landmark, review_summary, reviews), {
                **base_style,
                "display": "block",
            }
        else:
            raise PreventUpdate

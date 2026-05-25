from dash import ALL, Input, Output, ctx, html
from dash.exceptions import PreventUpdate

import ids
from backend.crud import get_landmark_image, get_landmark_review_summary, get_landmark_reviews
from backend.landmark_registry import LandmarkRegistry
from callbacks.utils.get_language import get_language_from_url
from callbacks.utils.trip_state import next_action_stop_index
from callbacks.widgets.info_widgets import build_empty_info, build_landmark_info, build_trip_info
from i18n import t


def _image_label(image, lang="bg"):
    if not image:
        return ""
    return image.get("commons_file") or t("info_sidebar.landmark_image", lang=lang)


def _image_tooltip(image, lang="bg"):
    if not image:
        return ""

    parts = [_image_label(image, lang=lang)]
    author = image.get("author")
    if author:
        parts.append(f"{t('info_sidebar.author', lang=lang)}: {author}")
    return "\n".join(part for part in parts if part)


def _image_meta(image, lang="bg"):
    if not image:
        return []

    children = [
        html.Div(_image_label(image, lang=lang), className="info-sidebar-image-label"),
    ]
    author = image.get("author")
    if author:
        children.append(html.Div(f"{t('info_sidebar.author', lang=lang)}: {author}", className="info-sidebar-image-author"))
    return children


def _learn_more_action(landmark, lang="bg"):
    if not landmark or not landmark.link or landmark.link == "#":
        return []
    return html.A(
        t("marker.learn_more", lang=lang),
        href=landmark.link,
        target="_blank",
        rel="noopener noreferrer",
        className="btn btn-outline-primary btn-sm",
    )


def register_info_callbacks(app):
    registry = LandmarkRegistry.get_landmarks()

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
        Input(ids.ACTIVE_INFO_STORE, "data", allow_optional=True),
        Input(ids.SELECTED_TRIP_STORE, "data"),
        Input(ids.MODE_STORE, "data", allow_optional=True),
        Input("url", "pathname"),
    )
    def render_info_sidebar(active_info, selected_trip, mode, pathname):
        lang = get_language_from_url(pathname)
        base_style = {
            "flex": "1 1 auto",
            "minHeight": 0,
            "overflowY": "auto",
        }
        hide_landmark_image = mode not in ("explore", "trip")
        browse_open = (pathname or "").rstrip("/").endswith("/browse")

        if browse_open:
            if selected_trip:
                trip_name = selected_trip.get("name") or t("info_sidebar.selected_trip", lang=lang)
                subtitle = t("info_sidebar.shared_trip", lang=lang) if selected_trip.get("source") == "shared" else t("info_sidebar.saved_trip", lang=lang)
                return trip_name, subtitle, [], True, None, "", True, None, "", [], build_trip_info(selected_trip, registry, lang=lang), {
                    **base_style,
                    "display": "block",
                    "overflow": "hidden",
                }
            return t("browse.title", lang=lang), t("info_sidebar.no_trip_selected", lang=lang), [], True, None, "", True, None, "", [], build_empty_info(lang=lang), {
                **base_style,
                "display": "block",
            }

        if not active_info:
            return t("info_sidebar.title", lang=lang), t("info_sidebar.no_selection", lang=lang), [], True, None, "", True, None, "", [], build_empty_info(lang=lang), {
                **base_style,
                "display": "block",
            }

        if active_info.get("type") in ("trip", "landmark"):
            landmark = registry.get_landmark(active_info.get("content"))
            if not landmark:
                title = t("trip_status.trip_complete", lang=lang) if active_info.get("type") == "trip" else t("info_sidebar.title", lang=lang)
                subtitle = t("trip_status.no_next_stop", lang=lang) if active_info.get("type") == "trip" else t("info_sidebar.no_selection", lang=lang)
                return title, subtitle, [], True, None, "", True, None, "", [], build_empty_info(lang=lang), {
                    **base_style,
                    "display": "block",
                }
            image = get_landmark_image(landmark.id)
            image_src = image.get("src_link") if image else None
            image_hidden = hide_landmark_image or not image_src
            image_source_url = image.get("image_source_url") or image_src if image else None
            image_alt = _image_label(image, lang=lang)
            image_title = _image_tooltip(image, lang=lang)
            review_summary = get_landmark_review_summary(landmark.id)
            reviews = get_landmark_reviews(landmark.id)
            return landmark.name, landmark.location, _learn_more_action(landmark, lang=lang), image_hidden, image_source_url, image_title, image_hidden, image_src, image_alt, _image_meta(image, lang=lang), build_landmark_info(landmark, review_summary, reviews, lang=lang), {
                **base_style,
                "display": "block",
            }
        else:
            raise PreventUpdate

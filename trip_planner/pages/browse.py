import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import ids
from backend.db.crud import get_user_trips
from callbacks.widgets.callback_widgets import build_load_trip_items
from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from i18n import t
from layout.info_sidebar import create_info_sidebar
from layout.sidebar import create_user_menu

dash.register_page(__name__, path_template="/<lang>/browse", name="Browse", order=1)


def layout(lang="bg", **kwargs):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    saved_trips = (
        get_user_trips(current_user.id, include_completion_status=True)
        if current_user.is_authenticated else
        []
    )
    return html.Div(
        [
            dcc.Store(id=ids.BROWSE_SAVED_TRIPS_STORE, data=saved_trips),
            dcc.Store(id=ids.BROWSE_SHARED_TRIPS_STORE, data=[]),
            dcc.Store(id=ids.SELECTED_TRIP_STORE, data=None),
            html.Div(id=ids.SELECTED_OBJECTS_GROUP, style={"display": "none"}),
            create_user_menu(lang=lang),
            create_info_sidebar(),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Link(
                                [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                                href=f"/{lang}",
                                className="btn btn-outline-secondary btn-sm",
                            ),
                            html.Div(
                                [
                                    html.H2(t("browse.title", lang=lang), className="mb-0"),
                                    html.Div(
                                        t("browse.subtitle", lang=lang),
                                        className="text-muted",
                                    ),
                                ],
                            ),
                        ],
                        className="d-flex align-items-center gap-3 mb-3",
                    ),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(
                                        id=ids.LOAD_TRIP_LIST,
                                        children=build_load_trip_items(saved_trips),
                                        flush=True,
                                    ),
                                    id=ids.MY_SAVED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100vh - 13rem)", "overflowY": "auto"},
                                ),
                                label=t("browse.my_saved_trips", lang=lang),
                                tab_id="my-saved-trips",
                            ),
                            dbc.Tab(
                                html.Div(
                                    dbc.ListGroup(id=ids.USER_SHARED_TRIPS_LIST, children=[], flush=True),
                                    id=ids.USER_SHARED_TRIPS_TAB,
                                    className="p-3",
                                    style={"height": "calc(100vh - 13rem)", "overflowY": "auto"},
                                ),
                                label=t("browse.user_shared_trips", lang=lang),
                                tab_id="user-shared-trips",
                            ),
                        ],
                        id=ids.BROWSE_TABS,
                        active_tab="my-saved-trips",
                    ),
                ],
                id=ids.PAGE_CONTENT,
                style={
                    "marginRight": "20rem",
                    "height": "100vh",
                    "overflow": "hidden",
                    "padding": "1.5rem",
                    "backgroundColor": "#f8f9fa",
                },
            ),
        ],
    )

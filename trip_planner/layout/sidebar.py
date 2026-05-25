import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_login import current_user

import ids
from styles import SIDEBAR_STYLE
from i18n import t


def create_selected_object_group():
    return dbc.ListGroup(
        id=ids.SELECTED_OBJECTS_GROUP,
        children=[],
        style={"flex": "1 1 auto", "minHeight": 0, "overflowY": "auto"},
    )


def create_landmark_search(initial_mode="explore", lang="bg"):
    return html.Div(
        dcc.Dropdown(
            id=ids.LANDMARK_SEARCH_DROPDOWN,
            options=[],
            placeholder=t("sidebar.search_landmark", lang=lang),
            searchable=True,
            clearable=True,
            className="landmark-search-dropdown",
            style={"fontSize": "0.9rem"},
        ),
        id=ids.LANDMARK_SEARCH_SHELL,
        className="landmark-search-shell",
        style={"display": "block" if initial_mode == "explore" else "none"},
    )


def create_trip_endpoints(lang="bg"):
    return html.Div(
        [
            html.Div([
                html.Label(t("sidebar.start_point", lang=lang), style={"fontSize": "11px", "marginBottom": "0"}),
                dbc.Select(
                    options=[{"label": t("sidebar.auto", lang=lang), "value": "auto"}],
                    placeholder=t("sidebar.select_start_point", lang=lang),
                    id=ids.START_POINT_DROPDOWN,
                    className="format-dropdown",
                    size=5,
                    style={"minHeight": "30px", "paddingTop": "0.2rem", "paddingBottom": "0.2rem", "fontSize": "0.85rem"},
                ),
            ]),
            html.Div([
                html.Label(t("sidebar.end_point", lang=lang), style={"fontSize": "11px", "marginBottom": "0"}),
                dbc.Select(
                    options=[{"label": t("sidebar.auto", lang=lang), "value": "auto"}],
                    placeholder=t("sidebar.select_end_point", lang=lang),
                    id=ids.END_POINT_DROPDOWN,
                    className="format-dropdown",
                    size=5,
                    style={"minHeight": "30px", "paddingTop": "0.2rem", "paddingBottom": "0.2rem", "fontSize": "0.85rem"},
                ),
            ]),
        ],
        style={
            "marginBottom": 0,
            "backgroundColor": "#E1E1E1",
            "border": "1px solid black",
            "padding": "0.35rem",
            "borderRadius": "0.25rem",
        },
    )


def create_sidebar(active_trip=None, lang="bg"):
    initial_mode = "trip" if active_trip else "explore"
    landmark_search = create_landmark_search(initial_mode, lang)
    route_endpoints = create_trip_endpoints(lang)
    selected_object_group = create_selected_object_group()
    optimize_route_btn = dbc.Button(
        [html.I(className="bi bi-signpost-split me-2"), t("sidebar.optimize_route", lang=lang)],
        color="success",
        className="mt-2",
        id=ids.OPTIMIZE_ROUTE_BTN,
    )
    save_trip_btn = dbc.Button(
        [html.I(className="bi bi-save me-2"), t("sidebar.save_trip", lang=lang)],
        color="secondary",
        className="mt-1",
        id=ids.SAVE_TRIP_BTN,
        disabled=True,
        style={"opacity": "0.45", "flex": "1"},
    )
    share_trip_btn = dbc.Button(
        [html.I(className="bi bi-share me-2"), t("sidebar.share_trip", lang=lang)],
        color="info",
        className="mt-1 w-100",
        id=ids.SHARE_TRIP_BTN,
    )

    mode_toggle = dbc.ButtonGroup(
        [
            dbc.Button(t("mode.explore", lang=lang), id=ids.MODE_BTN_EXPLORE, color="primary", outline=True, active=initial_mode == "explore", size="sm", style={"flex": "1"}),
            dbc.Button(t("mode.trip", lang=lang), id=ids.MODE_BTN_TRIP, color="primary", outline=True, active=initial_mode == "trip", size="sm", style={"flex": "1"}),
            dbc.Button(t("mode.browse", lang=lang), id=ids.MODE_BTN_BROWSE, color="primary", outline=True, active=False, size="sm", style={"flex": "1"}),
        ],
        className="w-100",
    )

    explore_panel = html.Div([
        route_endpoints,
        html.Div(
            dbc.Checklist(
                id=ids.HIDE_VISITED_LANDMARKS_FILTER,
                options=[{"label": t("sidebar.hide_visited_landmarks", lang=lang), "value": "hide_visited"}],
                value=[],
                switch=True,
                className="small",
                style={"margin": 0},
            ),
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Div([
            html.P(t("sidebar.selected_monuments", lang=lang), className="lead", style={"marginBottom": 0}),
            html.Span(
                t("sidebar.clear_all", lang=lang),
                id=ids.CLEAR_ALL_BTN,
                style={
                    "fontSize": "0.75rem",
                    "color": "#dc3545",
                    "cursor": "pointer",
                    "userSelect": "none",
                    "alignSelf": "center",
                },
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"}),
        selected_object_group,
        optimize_route_btn,
        html.Div([save_trip_btn], className="d-flex gap-2 w-100"),
    ], id=ids.EXPLORE_PANEL, style={"display": "flex" if initial_mode == "explore" else "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0})

    trip_panel = html.Div([
        html.Div(
            id=ids.TRIP_STATUS_PANEL,
            children=[
                dbc.Button(
                    t("sidebar.visit", lang=lang),
                    id=ids.TRIP_NEXT_VISIT_BTN,
                    disabled=True,
                    style={"display": "none"},
                ),
            ],
            style={
                "backgroundColor": "#F8F9FA",
                "border": "1px solid #D6D8DB",
                "borderRadius": "0.25rem",
                "padding": "0.75rem",
            },
        ),
        share_trip_btn,
    ], id=ids.TRIP_PANEL, style={"display": "flex" if initial_mode == "trip" else "none", "flexDirection": "column", "gap": "0.5rem", "flex": "1 1 auto", "minHeight": 0})

    return html.Div([
        html.Div([
            html.Div([
                html.Img(src="/assets/icon.svg", style={"height": "24px", "marginRight": "0.5rem"}),
                html.Span(t("app.name", lang=lang), style={"fontSize": "1.25rem", "fontWeight": "600"}),
            ], className="d-flex align-items-center justify-content-center"),
            html.Hr(style={"margin": 0}),
        ], style={"display": "flex", "flexDirection": "column", "gap": "0.25rem"}),
        mode_toggle,
        landmark_search,
        explore_panel,
        trip_panel,
    ], style={**SIDEBAR_STYLE, "gap": "0.5rem"}, id=ids.SIDEBAR)


def create_user_menu(fix_to_right=False, lang="bg"):
    username = current_user.id if current_user.is_authenticated else "User"
    right_offset = "0.75rem" if fix_to_right else "21rem"
    return dbc.DropdownMenu(
        id=ids.USER_MENU,
        label=html.I(className="bi bi-person-circle", style={"fontSize": "1.25rem", "color": "black"}),
        children=[
            dbc.DropdownMenuItem(
                [
                    html.Div(t("sidebar.signed_in_as", lang=lang), className="text-muted", style={"fontSize": "0.75rem"}),
                    html.Div(username, style={"fontWeight": "600"}),
                ],
                header=True,
            ),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                t("sidebar.statistics", lang=lang),
                href=f"/{lang}/statistics",
            ),
            dbc.DropdownMenuItem(divider=True),
            html.Div(
                [
                    html.Div(t("sidebar.language", lang=lang), className="text-muted", style={"fontSize": "0.75rem", "marginBottom": "0.25rem"}),
                    dbc.RadioItems(
                        id=ids.LANGUAGE_RADIO,
                        options=[
                            {"label": "Български", "value": "bg"},
                            {"label": "English", "value": "en"},
                        ],
                        value=lang,
                        inline=False,
                        className="small",

                    ),
                ],
                style={"margin-left": "0.5rem"},
            ),
            dbc.DropdownMenuItem(t("sidebar.logout", lang=lang), id=ids.LOGOUT_BUTTON, style={"color": "#dc3545"}),
        ],
        direction="down",
        align_end=True,
        toggle_style={
            "background": "none",
            "border": "none",
            "boxShadow": "none",
            "padding": "0.25rem 0.5rem",
            "color": "black",
        },
        style={
            "position": "fixed",
            "top": "0.75rem",
            "right": right_offset,
            "zIndex": 1050,
        },
    )

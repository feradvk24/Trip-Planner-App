from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from flask_login import login_user

import ids
from backend.auth import User, create_user, verify_user
from i18n import DEFAULT_LANGUAGE


def register_auth_callbacks(app):
    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children"),
        Output(ids.LOGIN_ALERT, "is_open"),
        Input(ids.LOGIN_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        prevent_initial_call=True,
    )
    def handle_login(n_clicks, username, password):
        if not n_clicks:
            raise PreventUpdate
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if verify_user(username, password):
            login_user(User(username))
            return f"/{DEFAULT_LANGUAGE}", "", False
        return no_update, "Invalid username or password.", True

    @app.callback(
        Output(ids.REGISTER_FIELDS, "style"),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.REGISTER_FIELDS, "style"),
        prevent_initial_call=True,
    )
    def toggle_register_fields(n_clicks, current_style):
        if not n_clicks:
            raise PreventUpdate
        if current_style and current_style.get("display") == "none":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "is_open", allow_duplicate=True),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        State(ids.REGISTER_FIRST_NAME, "value"),
        State(ids.REGISTER_LAST_NAME, "value"),
        State(ids.REGISTER_FIELDS, "style"),
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, username, password, first_name, last_name, fields_style):
        if not n_clicks:
            raise PreventUpdate
        if fields_style and fields_style.get("display") == "none":
            raise PreventUpdate
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if not first_name or not first_name.strip():
            return no_update, "Please enter your first name.", True
        if not last_name or not last_name.strip():
            return no_update, "Please enter your last name.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        if create_user(username, password, first_name.strip(), last_name.strip()):
            login_user(User(username))
            return f"/{DEFAULT_LANGUAGE}", "", False
        return no_update, "Username already exists.", True

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Input(ids.LOGOUT_BUTTON, "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_logout(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        from flask_login import logout_user as _logout
        _logout()
        return "/login"

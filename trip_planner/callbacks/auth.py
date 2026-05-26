from urllib.parse import parse_qs

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from flask_login import login_user

import ids
from backend.auth import AuthStatus, User, authenticate_user, create_user
from i18n import DEFAULT_LANGUAGE


def register_auth_callbacks(app):
    @app.callback(
        Output(ids.LOGIN_VERIFICATION_TOAST, "children"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "header"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "icon"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "is_open"),
        Input("url", "search"),
    )
    def show_verification_toast(search):
        if not search:
            raise PreventUpdate

        verified = parse_qs(search.lstrip("?")).get("verified", [None])[0]
        if verified == "1":
            return "Your email has been verified successfully.", "Email verified", "success", True
        if verified == "0":
            return "Failed to verify your email. The link may be invalid or expired.", "Verification failed", "danger", True

        raise PreventUpdate

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
        if len(username.strip()) < 6:
            return no_update, "Username must be at least 6 characters.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        auth_status = authenticate_user(username, password)
        if auth_status == AuthStatus.OK:
            login_user(User(username))
            return f"/{DEFAULT_LANGUAGE}", "", False
        if auth_status == AuthStatus.UNVERIFIED:
            return no_update, "Please verify your email before logging in.", True
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
        return no_update

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "children", allow_duplicate=True),
        Output(ids.LOGIN_ALERT, "is_open", allow_duplicate=True),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.LOGIN_USERNAME, "value"),
        State(ids.LOGIN_PASSWORD, "value"),
        State(ids.REGISTER_EMAIL, "value"),
        State(ids.REGISTER_FIRST_NAME, "value"),
        State(ids.REGISTER_LAST_NAME, "value"),
        State(ids.REGISTER_FIELDS, "style"),
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, username, password, email, first_name, last_name, fields_style):
        if not n_clicks:
            raise PreventUpdate
        if fields_style and fields_style.get("display") == "none":
            raise PreventUpdate
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if len(username.strip()) < 6:
            return no_update, "Username must be at least 6 characters.", True
        if not email or not email.strip():
            return no_update, "Please enter your email.", True
        if not first_name or not first_name.strip():
            return no_update, "Please enter your first name.", True
        if not last_name or not last_name.strip():
            return no_update, "Please enter your last name.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        if create_user(username.strip(), email.strip(), password, first_name.strip(), last_name.strip()):
            return no_update, "Registration successful. Please verify your email before logging in.", True
        return no_update, "Username or email already exists.", True

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

from urllib.parse import parse_qs
import re

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from flask_login import login_user, logout_user

from trip_planner import ids
from trip_planner.backend.auth import (
    AuthStatus,
    PasswordResetStatus,
    User,
    authenticate_user,
    create_user,
    is_admin_panel_role,
    request_password_reset,
    reset_password_with_token,
)
from trip_planner.backend.db.crud import get_user_auth_record
from trip_planner.i18n import DEFAULT_LANGUAGE


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def has_number(value):
    return any(character.isdigit() for character in value)


def is_valid_email(value):
    return bool(EMAIL_PATTERN.fullmatch(value))


def get_query_value(search, key):
    if not search:
        return None
    return parse_qs(search.lstrip("?")).get(key, [None])[0]


def register_auth_callbacks(app):
    @app.callback(
        Output(ids.LOGIN_VERIFICATION_TOAST, "children"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "header"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "icon"),
        Output(ids.LOGIN_VERIFICATION_TOAST, "is_open"),
        Input("url", "search"),
        Input("url", "pathname"),
    )
    def show_verification_toast(search, pathname):
        if pathname != "/login" or not search:
            raise PreventUpdate

        verified = get_query_value(search, "verified")
        registered = get_query_value(search, "registered")
        password_reset = get_query_value(search, "password_reset")
        if verified == "1":
            return "Your email has been verified successfully.", "Email verified", "success", True
        if verified == "0":
            return "Failed to verify your email. The link may be invalid or expired.", "Verification failed", "danger", True
        if registered == "1":
            return "Account created. Please check your email to verify your account.", "Registration successful", "success", True
        if password_reset == "1":
            return "Password changed successfully. You can now log in.", "Password changed", "success", True

        raise PreventUpdate

    @app.callback(
        Output(ids.PASSWORD_RESET_REQUEST_COLLAPSE, "is_open"),
        Input(ids.FORGOT_PASSWORD_BUTTON, "n_clicks"),
        State(ids.PASSWORD_RESET_REQUEST_COLLAPSE, "is_open"),
        prevent_initial_call=True,
    )
    def toggle_password_reset_request(n_clicks, is_open):
        if not n_clicks:
            raise PreventUpdate
        return not is_open

    @app.callback(
        Output(ids.PASSWORD_RESET_REQUEST_ALERT, "children"),
        Output(ids.PASSWORD_RESET_REQUEST_ALERT, "color"),
        Output(ids.PASSWORD_RESET_REQUEST_ALERT, "is_open"),
        Input(ids.PASSWORD_RESET_SEND_BUTTON, "n_clicks"),
        State(ids.PASSWORD_RESET_EMAIL, "value"),
        prevent_initial_call=True,
    )
    def handle_password_reset_request(n_clicks, email):
        if not n_clicks:
            raise PreventUpdate
        if not email or not email.strip():
            return "Please enter your email.", "danger", True
        if not is_valid_email(email.strip()):
            return "Please enter a valid email address.", "danger", True

        try:
            request_password_reset(email.strip())
        except Exception:
            return "Could not send the reset email. Please try again later.", "danger", True

        return "If an account exists for that email, a reset link has been sent.", "success", True

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.PASSWORD_RESET_ALERT, "children", allow_duplicate=True),
        Output(ids.PASSWORD_RESET_ALERT, "color", allow_duplicate=True),
        Output(ids.PASSWORD_RESET_ALERT, "is_open", allow_duplicate=True),
        Input(ids.PASSWORD_RESET_SUBMIT_BUTTON, "n_clicks"),
        State(ids.PASSWORD_RESET_NEW_PASSWORD, "value"),
        State(ids.PASSWORD_RESET_CONFIRM_PASSWORD, "value"),
        State("url", "search"),
        prevent_initial_call=True,
    )
    def handle_password_reset(n_clicks, new_password, confirm_password, search):
        if not n_clicks:
            raise PreventUpdate
        if not new_password or not confirm_password:
            return no_update, "Please enter and confirm your new password.", "danger", True
        if len(new_password) < 6:
            return no_update, "Password must be at least 6 characters.", "danger", True
        if new_password != confirm_password:
            return no_update, "Passwords do not match.", "danger", True

        status = reset_password_with_token(get_query_value(search, "password_reset_token"), new_password)
        if status == PasswordResetStatus.SUCCESS:
            logout_user()
            return "/login?password_reset=1", "", "success", False
        if status == PasswordResetStatus.EXPIRED:
            return no_update, "This password reset link has expired. Request a new reset link.", "danger", True
        return no_update, "This password reset link is invalid. Request a new reset link.", "danger", True

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
            user_record = get_user_auth_record(username)
            role = user_record["role"] if user_record else "regular"
            is_active = user_record["is_active"] if user_record else True
            login_user(User(username, role, is_active))
            if is_admin_panel_role(role):
                return "/admin_panel", "", False
            return f"/{DEFAULT_LANGUAGE}", "", False
        if auth_status == AuthStatus.INACTIVE:
            return no_update, "This user is inactive.", True
        if auth_status == AuthStatus.UNVERIFIED:
            return no_update, "Please verify your email before logging in.", True
        return no_update, "Invalid username or password.", True

    @app.callback(
        Output("url", "href", allow_duplicate=True),
        Output(ids.REGISTER_ALERT, "children"),
        Output(ids.REGISTER_ALERT, "is_open"),
        Input(ids.REGISTER_BUTTON, "n_clicks"),
        State(ids.REGISTER_USERNAME, "value"),
        State(ids.REGISTER_PASSWORD, "value"),
        State(ids.REGISTER_EMAIL, "value"),
        State(ids.REGISTER_FIRST_NAME, "value"),
        State(ids.REGISTER_LAST_NAME, "value"),
        prevent_initial_call=True,
    )
    def handle_register(n_clicks, username, password, email, first_name, last_name):
        if not n_clicks:
            raise PreventUpdate
        if not username or not password:
            return no_update, "Please enter both username and password.", True
        if len(username.strip()) < 6:
            return no_update, "Username must be at least 6 characters.", True
        if not email or not email.strip():
            return no_update, "Please enter your email.", True
        if not is_valid_email(email.strip()):
            return no_update, "Please enter a valid email address.", True
        if not first_name or not first_name.strip():
            return no_update, "Please enter your first name.", True
        if has_number(first_name.strip()):
            return no_update, "First name cannot contain numbers.", True
        if not last_name or not last_name.strip():
            return no_update, "Please enter your last name.", True
        if has_number(last_name.strip()):
            return no_update, "Last name cannot contain numbers.", True
        if len(password) < 6:
            return no_update, "Password must be at least 6 characters.", True
        if create_user(username.strip(), email.strip(), password, first_name.strip(), last_name.strip()):
            return "/login?registered=1", "", False
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

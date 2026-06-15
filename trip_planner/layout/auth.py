import dash_bootstrap_components as dbc
from dash import dcc, html

from trip_planner import ids


def create_login_layout(password_reset_token_valid=None):
    is_password_reset = password_reset_token_valid is not None
    login_form_style = {"display": "none"} if is_password_reset else {}
    password_reset_form_style = {} if is_password_reset else {"display": "none"}
    password_reset_alert = ""
    password_reset_alert_open = False
    password_reset_disabled = False
    if is_password_reset and not password_reset_token_valid:
        password_reset_alert = "This password reset link is invalid or expired. Request a new reset link."
        password_reset_alert_open = True
        password_reset_disabled = True

    return html.Div(
        dbc.Container([
            dbc.Row(dbc.Col(
                html.H2("Reset Password" if is_password_reset else "Login", className="text-center mb-4"),
                width=12,
            )),
            dbc.Row(dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Div([
                        dbc.Alert(id=ids.LOGIN_ALERT, is_open=False, color="danger", duration=4000),
                        dbc.Label("Username"),
                        dbc.Input(id=ids.LOGIN_USERNAME, placeholder="Enter username", className="mb-3"),
                        dbc.Label("Password"),
                        dbc.Input(id=ids.LOGIN_PASSWORD, type="password", placeholder="Enter password", className="mb-2"),
                        dbc.Button("Login", id=ids.LOGIN_BUTTON, color="primary", className="w-100 mb-2"),
                        dbc.Button("Login as guest", href="/guest", color="info", outline=True, className="w-100 mb-2"),
                        dbc.Button("Create account", href="/register", color="secondary", outline=True, className="w-100"),
                        dbc.Button(
                            "Forgotten password?",
                            id=ids.FORGOT_PASSWORD_BUTTON,
                            color="link",
                            className="d-block mx-auto p-0 mt-3 mb-3",
                        ),
                        dbc.Collapse([
                            dbc.Alert(
                                id=ids.PASSWORD_RESET_REQUEST_ALERT,
                                is_open=False,
                                color="success",
                                duration=5000,
                            ),
                            dbc.Label("Email"),
                            dbc.Input(
                                id=ids.PASSWORD_RESET_EMAIL,
                                type="email",
                                placeholder="Enter account email",
                                className="mb-2",
                            ),
                            dbc.Button(
                                "Send reset link",
                                id=ids.PASSWORD_RESET_SEND_BUTTON,
                                color="primary",
                                outline=True,
                                className="w-100 mb-3",
                            ),
                        ], id=ids.PASSWORD_RESET_REQUEST_COLLAPSE, is_open=False),
                    ], style=login_form_style),
                    html.Div([
                        dbc.Alert(
                            password_reset_alert,
                            id=ids.PASSWORD_RESET_ALERT,
                            is_open=password_reset_alert_open,
                            color="danger",
                        ),
                        dbc.Label("New password"),
                        dbc.Input(
                            id=ids.PASSWORD_RESET_NEW_PASSWORD,
                            type="password",
                            placeholder="Enter new password",
                            disabled=password_reset_disabled,
                            className="mb-3",
                        ),
                        dbc.Label("Confirm password"),
                        dbc.Input(
                            id=ids.PASSWORD_RESET_CONFIRM_PASSWORD,
                            type="password",
                            placeholder="Confirm new password",
                            disabled=password_reset_disabled,
                            className="mb-3",
                        ),
                        dbc.Button(
                            "Change password",
                            id=ids.PASSWORD_RESET_SUBMIT_BUTTON,
                            color="primary",
                            disabled=password_reset_disabled,
                            className="w-100 mb-2",
                        ),
                        dcc.Link("Back to login", href="/login", className="d-block text-center"),
                    ], style=password_reset_form_style),
                ]), className="shadow"),
                xs=12,
                sm={"size": 10, "offset": 1},
                md={"size": 6, "offset": 3},
                lg={"size": 4, "offset": 4},
                className="login-card-col",
            )),
            dbc.Toast(
                "",
                id=ids.LOGIN_VERIFICATION_TOAST,
                header="",
                icon="success",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": "1rem", "right": "1rem", "zIndex": 9999},
            ),
        ], className="login-container mt-5"),
        className="login-page",
        style={"minHeight": "100vh", "backgroundColor": "#f8f9fa"},
    )


def create_register_layout():
    return html.Div(
        dbc.Container([
            dbc.Row(dbc.Col(html.H2("Create Account", className="text-center mb-4"), width=12)),
            dbc.Row(dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Alert(id=ids.REGISTER_ALERT, is_open=False, color="danger", duration=4000),
                    dbc.Label("Username"),
                    dbc.Input(id=ids.REGISTER_USERNAME, placeholder="Enter username", className="mb-3"),
                    dbc.Label("Password"),
                    dbc.Input(id=ids.REGISTER_PASSWORD, type="password", placeholder="Enter password", className="mb-3"),
                    dbc.Label("Email"),
                    dbc.Input(id=ids.REGISTER_EMAIL, type="email", placeholder="Enter email", className="mb-3"),
                    dbc.Label("First name"),
                    dbc.Input(id=ids.REGISTER_FIRST_NAME, placeholder="Enter first name", className="mb-3"),
                    dbc.Label("Last name"),
                    dbc.Input(id=ids.REGISTER_LAST_NAME, placeholder="Enter last name", className="mb-3"),
                    dbc.Button("Create account", id=ids.REGISTER_BUTTON, color="primary", className="w-100 mb-2"),
                    dcc.Link("Back to login", href="/login", className="d-block text-center"),
                ]), className="shadow"),
                xs=12,
                sm={"size": 10, "offset": 1},
                md={"size": 6, "offset": 3},
                lg={"size": 4, "offset": 4},
                className="login-card-col",
            )),
        ], className="login-container mt-5"),
        className="login-page",
        style={"minHeight": "100vh", "backgroundColor": "#f8f9fa"},
    )

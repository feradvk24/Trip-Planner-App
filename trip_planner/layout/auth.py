import dash_bootstrap_components as dbc
from dash import html

import ids


def create_login_layout():
    return html.Div(
        dbc.Container([
            dbc.Row(dbc.Col(html.H2("Trip Planner Login", className="text-center mb-4"), width=12)),
            dbc.Row(dbc.Col(
                dbc.Card(dbc.CardBody([
                    dbc.Alert(id=ids.LOGIN_ALERT, is_open=False, color="danger", duration=4000),
                    dbc.Label("Username"),
                    dbc.Input(id=ids.LOGIN_USERNAME, placeholder="Enter username", className="mb-3"),
                    dbc.Label("Password"),
                    dbc.Input(id=ids.LOGIN_PASSWORD, type="password", placeholder="Enter password", className="mb-3"),
                    html.Div(id=ids.REGISTER_FIELDS, style={"display": "none"}, children=[
                        dbc.Label("Email"),
                        dbc.Input(id=ids.REGISTER_EMAIL, type="email", placeholder="Enter email", className="mb-3"),
                        dbc.Label("First name"),
                        dbc.Input(id=ids.REGISTER_FIRST_NAME, placeholder="Enter first name", className="mb-3"),
                        dbc.Label("Last name"),
                        dbc.Input(id=ids.REGISTER_LAST_NAME, placeholder="Enter last name", className="mb-3"),
                    ]),
                    dbc.Button("Login", id=ids.LOGIN_BUTTON, color="primary", className="w-100 mb-2"),
                    dbc.Button("Register", id=ids.REGISTER_BUTTON, color="secondary", outline=True, className="w-100"),
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

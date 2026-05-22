import os
from typing import Optional

import requests


def _current_request_cookie_headers() -> dict:
    try:
        from flask import has_request_context, request
    except ImportError:
        return {}

    if not has_request_context() or not request.headers.get("Cookie"):
        return {}
    return {"Cookie": request.headers["Cookie"]}


def post_json_to_endpoint(
    endpoint_path: str,
    payload: dict,
    external_url_env: str,
    error_prefix: str,
) -> Optional[dict]:
    external_url = os.environ.get(external_url_env)
    if external_url:
        response = requests.post(external_url, json=payload, timeout=20)
        if response.status_code != 200:
            raise Exception(f"{error_prefix}: {response.status_code}")
        return response.json()

    try:
        from flask import current_app, has_app_context, has_request_context
    except ImportError:
        return None

    if not has_app_context() or not has_request_context():
        return None

    response = current_app.test_client(use_cookies=False).post(
        endpoint_path,
        json=payload,
        headers=_current_request_cookie_headers(),
    )
    if response.status_code != 200:
        error = response.get_json(silent=True) or {}
        message = error.get("error") or f"{error_prefix}: {response.status_code}"
        raise Exception(message)
    return response.get_json()

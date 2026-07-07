"""One-time app code -> JWT exchange for Streamlit apps.

The app receives a single-use ``gws_code`` in its URL (minted by the lab launcher / gateway) and
swaps it here for a JWT it then carries on data lab API calls. This module is intentionally
**gws_core-free** (it may run in a virtual-env app without gws_core): it only uses ``requests`` and
env vars.
"""

import os

import requests

# core-api route path — duplicated here because gws_streamlit_base cannot import gws_core.
# Mirrors gws_core Settings.core_api_route_path().
_CORE_API_ROUTE_PATH = "core-api"
_EXCHANGE_TIMEOUT_SECONDS = 10
_HTTP_OK = 200


class ExchangedUser:
    """Result of a successful code exchange: the JWT to carry, and the resolved user id."""

    def __init__(self, user_access_token: str, user_id: str):
        self.user_access_token = user_access_token
        self.user_id = user_id


def exchange_code_for_jwt(app_id: str, code: str) -> ExchangedUser | None:
    """Exchange a one-time app code for a JWT + user id, or None on failure.

    :param app_id: the app the code was minted for (GWS_APP_ID)
    :param code: the one-time code from the ``gws_code`` query param
    :return: the exchanged user, or None if the code is invalid/expired or the call fails
    """
    lab_api_url = (os.environ.get("GWS_LAB_API_URL") or "").rstrip("/")
    if not lab_api_url:
        return None

    url = f"{lab_api_url}/{_CORE_API_ROUTE_PATH}/apps/exchange-code"

    try:
        response = requests.post(
            url,
            json={"app_id": app_id, "code": code},
            timeout=_EXCHANGE_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return None

    if response.status_code != _HTTP_OK:
        return None

    data = response.json()
    return ExchangedUser(
        user_access_token=data["user_access_token"],
        user_id=data["user_id"],
    )


def validate_jwt_for_user(app_id: str, jwt: str) -> str | None:
    """Validate a session JWT (from the gws_app_jwt cookie) and return the user id, or None.

    Used on a fresh page load (F5 / new tab): the app has no one-time code but holds the JWT it
    stored in a cookie on first load. It cannot validate the JWT itself (no gws_core / no secret),
    so it relays it to the lab.

    :param app_id: the app the JWT is used for (GWS_APP_ID)
    :param jwt: the JWT from the ``gws_app_jwt`` cookie
    :return: the resolved user id, or None if the JWT is invalid/expired or the call fails
    """
    lab_api_url = (os.environ.get("GWS_LAB_API_URL") or "").rstrip("/")
    if not lab_api_url:
        return None

    url = f"{lab_api_url}/{_CORE_API_ROUTE_PATH}/apps/validate-jwt"

    try:
        response = requests.post(
            url,
            json={"app_id": app_id, "jwt": jwt},
            timeout=_EXCHANGE_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return None

    if response.status_code != _HTTP_OK:
        return None

    return response.json().get("user_id")

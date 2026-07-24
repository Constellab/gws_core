"""Constellab device-code login, used as the identity step of the MCP OAuth flow.

This drives the same community endpoints as ``gws community login``
(``/cli-auth/code`` then ``/cli-auth/token``), but from inside the lab rather
than from the CLI: the CLI's implementation lives in ``gws_cli`` which the brick
cannot import.

Scope of this module: obtain a Constellab identity (an email) in a browser. It
deliberately stops there -- the token Constellab returns authenticates against
the *community* API and is never used as a lab credential. Mapping that identity
to a lab user and minting the lab JWT is the provider's job
(``mcp_oauth_provider``).
"""

import base64
import json

from fastapi import status

from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings

# A base64url payload is padded to a multiple of 4 characters.
_BASE64_BLOCK_SIZE = 4


class ConstellabLoginError(Exception):
    """Raised when the Constellab login cannot be started or completed."""


class ConstellabLoginService:
    """Client for the Constellab CLI-auth (device code) endpoints."""

    @classmethod
    def request_device_code(cls) -> tuple[str, str]:
        """Start a login: ask Constellab for a device code and its browser URL.

        :return: Tuple of (device_code, auth_url) -- the URL the user must open.
        :raises ConstellabLoginError: If the community server cannot be reached.
        """
        url = f"{cls._get_community_api_url()}/cli-auth/code"

        try:
            response = ExternalApiService.post(url, {}, raise_exception_if_error=True, timeout=30)
        except Exception as err:
            raise ConstellabLoginError(
                "Cannot reach the Constellab community server to start the login."
            ) from err

        data = response.json()
        if not isinstance(data, dict) or "code" not in data:
            raise ConstellabLoginError(
                "Unexpected response from Constellab when requesting an authorization code."
            )

        code = data["code"]
        auth_url = data.get("authUrl") or f"{cls._get_community_front_url()}/cli-auth?code={code}"
        return code, auth_url

    @classmethod
    def poll_for_token(cls, device_code: str) -> str | None:
        """Check once whether the user has completed the browser login.

        Non-blocking by design: the caller (an HTTP route) must not hold a
        request open for minutes, unlike the CLI which can block.

        :param device_code: The code returned by :meth:`request_device_code`.
        :return: The Constellab access token, or ``None`` if still pending.
        :raises ConstellabLoginError: If the login was denied or expired.
        """
        url = f"{cls._get_community_api_url()}/cli-auth/token"

        try:
            response = ExternalApiService.post(
                url, {"code": device_code}, raise_exception_if_error=False, timeout=30
            )
        except Exception:
            # Network blip: treat as "still pending" so the caller retries.
            return None

        if response.status_code == status.HTTP_410_GONE:
            raise ConstellabLoginError("The login request expired. Please retry.")
        if response.status_code == status.HTTP_409_CONFLICT:
            raise ConstellabLoginError("The login was denied.")

        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        login_status = str(data.get("status", "")).lower()
        if "expired" in login_status:
            raise ConstellabLoginError("The login request expired. Please retry.")
        if "denied" in login_status or "refused" in login_status:
            raise ConstellabLoginError("The login was denied.")

        if (
            response.status_code < status.HTTP_200_OK
            or response.status_code >= status.HTTP_300_MULTIPLE_CHOICES
        ):
            return None

        return data.get("token") or data.get("accessToken") or data.get("access_token")

    @classmethod
    def get_email_from_token(cls, access_token: str) -> str:
        """Extract the Constellab identity (email) from the community token.

        The token is *not* verified here: it was just delivered over TLS by the
        community server in response to a code only we hold, and it is used only
        to look up an existing lab user (who must be active). It never grants
        lab access by itself.

        :param access_token: The Constellab access token.
        :return: The user's email.
        :raises ConstellabLoginError: If no email can be read from the token.
        """
        email = cls._read_jwt_claim(access_token, "email")
        if not email:
            raise ConstellabLoginError(
                "Could not read the account email from the Constellab response."
            )
        return email

    @staticmethod
    def _read_jwt_claim(token: str, claim: str) -> str | None:
        """Read a claim from a JWT payload without verifying the signature."""
        try:
            payload_b64 = token.split(".")[1]
            padding = _BASE64_BLOCK_SIZE - len(payload_b64) % _BASE64_BLOCK_SIZE
            if padding != _BASE64_BLOCK_SIZE:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            value = payload.get(claim)
            return str(value) if value is not None else None
        except Exception:
            return None

    @staticmethod
    def _get_community_api_url() -> str:
        return Settings.get_community_api_url_and_check()

    @staticmethod
    def _get_community_front_url() -> str:
        return Settings.get_community_front_url_and_check()

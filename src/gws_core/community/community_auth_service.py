import base64
import json
import os
import time
import webbrowser
from dataclasses import dataclass

import requests
import typer

from .community_credential_service import CommunityCredentialService


class AuthorizationExpiredError(Exception):
    pass


class AuthorizationDeniedError(Exception):
    pass


@dataclass
class TokenInfo:
    """Holds the access token and optional expiration timestamp."""

    access_token: str
    expires_at: float | None = None


class CommunityAuthService:
    """Service for community authentication via the OAuth device-code flow.

    Handles the browser-based login flow (device code request, polling, browser opening)
    and delegates credential storage to CommunityCredentialService via composition.
    """

    _credential_service = CommunityCredentialService

    POLL_INTERVAL_SECONDS = 5
    POLL_TIMEOUT_SECONDS = 600  # 10 minutes

    @staticmethod
    def request_device_code() -> tuple[str, str]:
        """Request a device code from the community API.

        :return: Tuple of (code, auth_url)
        :raises Exception: If the server cannot be reached
        """
        api_url = CommunityAuthService._credential_service.get_community_api_url()
        url = f"{api_url}/cli-auth/code"

        try:
            response = requests.post(url, json={}, timeout=30)
        except requests.exceptions.RequestException as err:
            raise Exception(
                "Cannot reach the Community server. Please check your connection."
            ) from err

        if response.status_code < 200 or response.status_code >= 300:
            raise Exception(f"Failed to request authorization code (HTTP {response.status_code}).")

        try:
            data = response.json()
        except ValueError as err:
            raise Exception(
                "Unexpected response from the Community server when requesting authorization code."
            ) from err
        if not isinstance(data, dict) or "code" not in data:
            raise Exception(
                "Unexpected response format from the Community server when requesting authorization code."
            ) from None
        auth_url = data.get("authUrl", "")
        return data["code"], auth_url

    @staticmethod
    def _extract_jwt_expiration(token: str) -> float | None:
        """Extract the exp claim from a JWT token without verifying the signature."""
        try:
            payload_b64 = token.split(".")[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            exp = payload.get("exp")
            return float(exp) if exp is not None else None
        except Exception:
            return None

    @staticmethod
    def _parse_poll_response(response: requests.Response) -> TokenInfo | None:
        """Parse a poll response and return token info if available.

        :return: TokenInfo with access_token and optional expires_at, or None if still pending
        :raises AuthorizationExpiredError: If the code has expired
        :raises AuthorizationDeniedError: If the authorization was denied
        """
        if response.status_code == 410:
            raise AuthorizationExpiredError()
        if response.status_code == 409:
            raise AuthorizationDeniedError()

        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        # Check status field from response body
        status = data.get("status", "").lower()
        if "expired" in status:
            raise AuthorizationExpiredError()
        if "denied" in status or "refused" in status:
            raise AuthorizationDeniedError()

        # Check for error HTTP codes with message fallback
        if response.status_code < 200 or response.status_code >= 300:
            message = data.get("message", "").lower()
            if "expired" in message:
                raise AuthorizationExpiredError()
            if "denied" in message or "already" in message:
                raise AuthorizationDeniedError()
            return None

        # Success: extract token
        access_token = data.get("token") or data.get("accessToken") or data.get("access_token")
        if not access_token:
            return None

        # Extract expiration: from response fields or from JWT payload
        expires_at: float | None = None
        if "expiresAt" in data:
            expires_at = float(data["expiresAt"])
        elif "expires_at" in data:
            expires_at = float(data["expires_at"])
        elif "expiresIn" in data:
            expires_at = time.time() + float(data["expiresIn"])
        elif "expires_in" in data:
            expires_at = time.time() + float(data["expires_in"])
        else:
            # Fallback: decode the JWT to extract the exp claim
            expires_at = CommunityAuthService._extract_jwt_expiration(access_token)

        return TokenInfo(access_token=access_token, expires_at=expires_at)

    @staticmethod
    def poll_for_token(code: str) -> TokenInfo:
        """Poll the community API for an access token.

        :param code: The device code to exchange
        :return: TokenInfo with access_token and optional expires_at
        :raises AuthorizationExpiredError: If the code has expired
        :raises AuthorizationDeniedError: If the authorization was denied
        """
        api_url = CommunityAuthService._credential_service.get_community_api_url()
        url = f"{api_url}/cli-auth/token"
        start_time = time.monotonic()

        while True:
            time.sleep(CommunityAuthService.POLL_INTERVAL_SECONDS)

            if time.monotonic() - start_time >= CommunityAuthService.POLL_TIMEOUT_SECONDS:
                raise AuthorizationExpiredError()

            try:
                response = requests.post(url, json={"code": code}, timeout=30)
            except requests.exceptions.RequestException:
                # Network error: retry silently
                continue

            token_info = CommunityAuthService._parse_poll_response(response)
            if token_info:
                return token_info

    @staticmethod
    def open_browser(url: str) -> bool:
        """Try to open a URL in the default browser.

        :return: True if the browser was opened successfully, False otherwise
        """
        try:
            # Redirect stderr to suppress noisy errors from webbrowser (e.g. VS Code socket errors)
            devnull = os.open(os.devnull, os.O_WRONLY)
            old_stderr = os.dup(2)
            os.dup2(devnull, 2)
            try:
                return webbrowser.open(url)
            finally:
                os.dup2(old_stderr, 2)
                os.close(devnull)
                os.close(old_stderr)
        except Exception:
            return False

    @staticmethod
    def run_login_flow(force: bool = False) -> None:
        """Run the full OAuth device-code login flow.

        :param force: If True, re-authenticate even if already logged in
        """
        domain = CommunityAuthService._credential_service.get_current_api_domain()

        # Check if already logged in (with a valid, non-expired token)
        if not force and CommunityAuthService._credential_service.has_credentials(domain):
            typer.echo(f"You are already logged in to {domain}. Use --force to re-authenticate.")
            return

        # If token exists but expired, inform the user
        if not force and CommunityAuthService._credential_service.is_token_expired(domain):
            typer.echo(f"Your session on {domain} has expired. Re-authenticating...")

        # Step 1: Request device code
        try:
            code, auth_url = CommunityAuthService.request_device_code()
        except Exception as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)

        # Step 2: Open browser
        # Use authUrl from the backend if available, otherwise build it
        if not auth_url:
            front_url = CommunityAuthService._credential_service.get_community_front_url()
            auth_url = f"{front_url}/cli-auth?code={code}"

        browser_opened = CommunityAuthService.open_browser(auth_url)
        if browser_opened:
            typer.echo("\nBrowser opened for authentication.")
            typer.echo(
                f"If the browser didn't open, copy and paste this URL manually:\n{auth_url}\n"
            )
        else:
            typer.echo("\nCould not open the browser automatically.")
            typer.echo(f"Please open the following URL manually in your browser:\n{auth_url}\n")

        typer.echo("Waiting for authorization...\n")

        # Step 3: Poll for token
        try:
            token_info = CommunityAuthService.poll_for_token(code)
        except AuthorizationExpiredError:
            typer.echo(
                "The authorization code has expired. Run `gws community login` to try again.",
                err=True,
            )
            raise typer.Exit(1)
        except AuthorizationDeniedError:
            typer.echo(
                "Authorization was denied. Run `gws community login` to try again.", err=True
            )
            raise typer.Exit(1)

        # Step 4: Save token with domain and expiration
        CommunityAuthService._credential_service.save_credentials(
            access_token=token_info.access_token,
            expires_at=token_info.expires_at,
            domain=domain,
        )
        typer.echo(f"Authentication successful! You are now logged in to {domain}.")

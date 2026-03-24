import base64
import json
import os
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import requests
import typer
from gws_core.community.community_user_service import CommunityUserService
from gws_core.core.utils.settings import Settings


class AuthorizationExpiredError(Exception):
    pass


class AuthorizationDeniedError(Exception):
    pass


class TokenExpiredError(Exception):
    pass


@dataclass
class TokenInfo:
    """Holds the access token and optional expiration timestamp."""

    access_token: str
    expires_at: float | None = None


class CommunityCliService:
    GWS_CLI_CONFIG_DIR = Path.home() / ".gws"
    GWS_CLI_CREDENTIALS_FILE = GWS_CLI_CONFIG_DIR / "credentials.json"

    POLL_INTERVAL_SECONDS = 5
    POLL_TIMEOUT_SECONDS = 600  # 10 minutes

    # ------------------------------------------------------------------ #
    #  Credential storage (per-domain)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_all_credentials() -> dict:
        """Load the full credentials file as a dict keyed by domain."""
        if not CommunityCliService.GWS_CLI_CREDENTIALS_FILE.exists():
            return {}
        try:
            data = json.loads(
                CommunityCliService.GWS_CLI_CREDENTIALS_FILE.read_text(encoding="utf-8")
            )
            # Migration: old format was {"access_token": "..."}
            if isinstance(data, dict) and "access_token" in data and "credentials" not in data:
                return {}
            return data.get("credentials", {}) if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save_all_credentials(credentials: dict) -> None:
        """Write the full credentials dict to disk."""
        CommunityCliService.GWS_CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.write_text(
            json.dumps({"credentials": credentials}, indent=2), encoding="utf-8"
        )
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.chmod(0o600)

    @staticmethod
    def _get_current_api_domain() -> str:
        """Return the community API URL that the CLI is currently targeting."""
        try:
            return CommunityUserService.get_community_api_url()
        except Exception:
            return "https://api.constellab.community"

    @staticmethod
    def save_credentials(access_token: str, expires_at: float | None = None,
                         domain: str | None = None) -> None:
        """Save access token for a given domain."""
        if domain is None:
            domain = CommunityCliService._get_current_api_domain()
        all_creds = CommunityCliService._load_all_credentials()
        entry: dict = {"access_token": access_token}
        if expires_at is not None:
            entry["expires_at"] = expires_at
        all_creds[domain] = entry
        CommunityCliService._save_all_credentials(all_creds)

    @staticmethod
    def load_credentials(domain: str | None = None) -> tuple[str | None, float | None]:
        """Load access token and expiration for the given (or current) domain.

        :return: Tuple of (access_token, expires_at) or (None, None)
        """
        if domain is None:
            domain = CommunityCliService._get_current_api_domain()
        all_creds = CommunityCliService._load_all_credentials()
        entry = all_creds.get(domain)
        if entry is None:
            return None, None
        return entry.get("access_token"), entry.get("expires_at")

    @staticmethod
    def load_access_token(domain: str | None = None) -> str | None:
        """Load a valid (non-expired) access token for the given domain."""
        access_token, expires_at = CommunityCliService.load_credentials(domain)
        if access_token is None:
            return None
        if expires_at is not None and time.time() >= expires_at:
            return None
        return access_token

    @staticmethod
    def delete_credentials(domain: str | None = None) -> None:
        """Delete credentials for a specific domain."""
        if domain is None:
            domain = CommunityCliService._get_current_api_domain()
        all_creds = CommunityCliService._load_all_credentials()
        if domain in all_creds:
            del all_creds[domain]
            CommunityCliService._save_all_credentials(all_creds)

    @staticmethod
    def delete_all_credentials() -> None:
        """Delete credentials for all domains."""
        if CommunityCliService.GWS_CLI_CREDENTIALS_FILE.exists():
            CommunityCliService.GWS_CLI_CREDENTIALS_FILE.unlink()

    @staticmethod
    def has_credentials(domain: str | None = None) -> bool:
        """Check if valid (non-expired) credentials exist for the domain."""
        return CommunityCliService.load_access_token(domain) is not None

    @staticmethod
    def is_token_expired(domain: str | None = None) -> bool:
        """Check if a token exists but is expired."""
        access_token, expires_at = CommunityCliService.load_credentials(domain)
        if access_token is None:
            return False
        if expires_at is None:
            return False
        return time.time() >= expires_at

    @staticmethod
    def get_stored_domains() -> list[str]:
        """Return all domains that have stored credentials."""
        return list(CommunityCliService._load_all_credentials().keys())

    @staticmethod
    def get_community_service(requires_authentication: bool = False) -> CommunityUserService:
        """Create a CommunityUserService with the stored access token.

        :param requires_authentication: If True, raise an error when no valid access token is found.
        """
        domain = CommunityCliService._get_current_api_domain()
        access_token = CommunityCliService.load_access_token(domain)

        if requires_authentication and not access_token:
            if CommunityCliService.is_token_expired(domain):
                raise TokenExpiredError(
                    "Your session has expired. Please run 'gws community login' to re-authenticate."
                )
            raise Exception(
                "You are not authenticated. Please run 'gws community login' first."
            )
        return CommunityUserService(access_token=access_token)

    @staticmethod
    def get_community_front_url() -> str:
        """Get the community front URL."""
        # return "https://community-api-pre-prod.constellab-pre-prod.gencovery.com"
        return Settings.get_community_front_url_and_check()

    @classmethod
    def get_community_api_url(cls) -> str:
        """Get the community API URL, preferring environment variable over settings."""
        # return "https://community-api-pre-prod.constellab-pre-prod.gencovery.com"
        # return "https://api.constellab.community"
        return Settings.get_community_api_url_and_check()

    @staticmethod
    def request_device_code() -> tuple[str, str]:
        """Request a device code from the community API.

        :return: Tuple of (code, auth_url)
        :raises Exception: If the server cannot be reached
        """
        api_url = CommunityCliService.get_community_api_url()
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
            expires_at = CommunityCliService._extract_jwt_expiration(access_token)

        return TokenInfo(access_token=access_token, expires_at=expires_at)

    @staticmethod
    def poll_for_token(code: str) -> TokenInfo:
        """Poll the community API for an access token.

        :param code: The device code to exchange
        :return: TokenInfo with access_token and optional expires_at
        :raises AuthorizationExpiredError: If the code has expired
        :raises AuthorizationDeniedError: If the authorization was denied
        """
        api_url = CommunityCliService.get_community_api_url()
        url = f"{api_url}/cli-auth/token"
        start_time = time.monotonic()

        while True:
            time.sleep(CommunityCliService.POLL_INTERVAL_SECONDS)

            if time.monotonic() - start_time >= CommunityCliService.POLL_TIMEOUT_SECONDS:
                raise AuthorizationExpiredError()

            try:
                response = requests.post(url, json={"code": code}, timeout=30)
            except requests.exceptions.RequestException:
                # Network error: retry silently
                continue

            token_info = CommunityCliService._parse_poll_response(response)
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
        domain = CommunityCliService._get_current_api_domain()

        # Check if already logged in (with a valid, non-expired token)
        if not force and CommunityCliService.has_credentials(domain):
            typer.echo(f"You are already logged in to {domain}. Use --force to re-authenticate.")
            return

        # If token exists but expired, inform the user
        if not force and CommunityCliService.is_token_expired(domain):
            typer.echo(f"Your session on {domain} has expired. Re-authenticating...")

        # Step 1: Request device code
        try:
            code, auth_url = CommunityCliService.request_device_code()
        except Exception as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)

        # Step 2: Open browser
        # Use authUrl from the backend if available, otherwise build it
        if not auth_url:
            front_url = CommunityCliService.get_community_front_url()
            auth_url = f"{front_url}/cli-auth?code={code}"

        browser_opened = CommunityCliService.open_browser(auth_url)
        if browser_opened:
            typer.echo("\nBrowser opened for authentication.")
            typer.echo(f"If the browser didn't open, copy and paste this URL manually:\n{auth_url}\n")
        else:
            typer.echo("\nCould not open the browser automatically.")
            typer.echo(f"Please open the following URL manually in your browser:\n{auth_url}\n")

        typer.echo("Waiting for authorization...\n")

        # Step 3: Poll for token
        try:
            token_info = CommunityCliService.poll_for_token(code)
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
        CommunityCliService.save_credentials(
            access_token=token_info.access_token,
            expires_at=token_info.expires_at,
            domain=domain,
        )
        typer.echo(f"Authentication successful! You are now logged in to {domain}.")

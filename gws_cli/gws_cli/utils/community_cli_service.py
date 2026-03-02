import json
import time
import webbrowser
from pathlib import Path

import requests
import typer

from gws_core.community.community_user_service import CommunityUserService
from gws_core.core.utils.settings import Settings


class AuthorizationExpiredError(Exception):
    pass


class AuthorizationDeniedError(Exception):
    pass


class CommunityCliService:
    GWS_CLI_CONFIG_DIR = Path.home() / ".gws"
    GWS_CLI_CREDENTIALS_FILE = GWS_CLI_CONFIG_DIR / "credentials.json"

    POLL_INTERVAL_SECONDS = 5

    @staticmethod
    def save_credentials(access_token: str) -> None:
        """Save access token to the credentials file."""
        CommunityCliService.GWS_CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        credentials = {"access_token": access_token}
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.write_text(
            json.dumps(credentials, indent=2), encoding="utf-8"
        )
        # Restrict file permissions to owner only
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.chmod(0o600)

    @staticmethod
    def load_access_token() -> str | None:
        """Load access token from the credentials file."""
        if not CommunityCliService.GWS_CLI_CREDENTIALS_FILE.exists():
            return None
        credentials = json.loads(
            CommunityCliService.GWS_CLI_CREDENTIALS_FILE.read_text(encoding="utf-8")
        )
        return credentials.get("access_token")

    @staticmethod
    def delete_credentials() -> None:
        """Delete the credentials file."""
        if CommunityCliService.GWS_CLI_CREDENTIALS_FILE.exists():
            CommunityCliService.GWS_CLI_CREDENTIALS_FILE.unlink()

    @staticmethod
    def has_credentials() -> bool:
        """Check if credentials exist."""
        return CommunityCliService.load_access_token() is not None

    @staticmethod
    def get_community_service(requires_authentication: bool = False) -> CommunityUserService:
        """Create a CommunityUserService with the stored access token.

        :param requires_authentication: If True, raise an error when no access token is found.
        """
        access_token = CommunityCliService.load_access_token()
        if requires_authentication and not access_token:
            raise Exception(
                "You are not authenticated. Please run 'gws community login' first."
            )
        return CommunityUserService(access_token=access_token)

    @staticmethod
    def get_community_front_url() -> str:
        """Get the community front URL."""
        try:
            url = Settings.get_community_front_url()
            if url:
                return url
        except Exception:
            pass
        return "https://constellab.community"

    @staticmethod
    def request_device_code() -> tuple[str, str]:
        """Request a device code from the community API.

        :return: Tuple of (code, auth_url)
        :raises Exception: If the server cannot be reached
        """
        api_url = CommunityUserService.get_community_api_url()
        url = f"{api_url}/cli-auth/code"

        try:
            response = requests.post(url, json={}, timeout=30)
        except requests.exceptions.RequestException:
            raise Exception("Cannot reach the Community server. Please check your connection.")

        if response.status_code < 200 or response.status_code >= 300:
            raise Exception(f"Failed to request authorization code (HTTP {response.status_code}).")

        data = response.json()
        return data["code"], data.get("authUrl", "")

    @staticmethod
    def poll_for_token(code: str) -> str:
        """Poll the community API for an access token.

        :param code: The device code to exchange
        :return: The access token
        :raises AuthorizationExpiredError: If the code has expired
        :raises AuthorizationDeniedError: If the authorization was denied
        """
        api_url = CommunityUserService.get_community_api_url()
        url = f"{api_url}/cli-auth/token"

        while True:
            time.sleep(CommunityCliService.POLL_INTERVAL_SECONDS)

            try:
                response = requests.post(url, json={"code": code}, timeout=30)
            except requests.exceptions.RequestException:
                # Network error: retry silently
                continue

            if response.status_code == 410:
                raise AuthorizationExpiredError()

            if response.status_code == 409:
                raise AuthorizationDeniedError()

            try:
                data = response.json()
            except ValueError:
                continue

            if not isinstance(data, dict):
                continue

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
                # Unknown error: retry silently
                continue

            # Success: extract token
            access_token = data.get("token") or data.get("accessToken") or data.get("access_token")
            if access_token:
                return access_token

            # Pending (status=authorization_pending): continue polling

    @staticmethod
    def open_browser(url: str) -> None:
        """Try to open a URL in the default browser."""
        try:
            webbrowser.open(url)
        except Exception:
            pass

    @staticmethod
    def run_login_flow(force: bool = False) -> None:
        """Run the full OAuth device-code login flow.

        :param force: If True, re-authenticate even if already logged in
        """
        # Check if already logged in
        if not force and CommunityCliService.has_credentials():
            typer.echo("You are already logged in. Use --force to re-authenticate.")
            return

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

        typer.echo("\nOpening browser for authentication...")
        typer.echo(f"{auth_url}\n")
        typer.echo("If the browser didn't open, copy and paste the URL above.\n")
        CommunityCliService.open_browser(auth_url)

        typer.echo("Waiting for authorization...\n")

        # Step 3: Poll for token
        try:
            access_token = CommunityCliService.poll_for_token(code)
        except AuthorizationExpiredError:
            typer.echo("The authorization code has expired. Run `gws community login` to try again.", err=True)
            raise typer.Exit(1)
        except AuthorizationDeniedError:
            typer.echo("Authorization was denied. Run `gws community login` to try again.", err=True)
            raise typer.Exit(1)

        # Step 4: Save token
        CommunityCliService.save_credentials(access_token)
        typer.echo("Authentication successful! You are now logged in.")

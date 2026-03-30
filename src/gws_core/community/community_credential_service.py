import json
import time
from pathlib import Path

from ..core.utils.settings import Settings


class CommunityCredentialService:
    """Service for managing community API credentials (stored per-domain).

    Handles credential storage and retrieval of access tokens.
    This service has no CLI dependencies and can be used from any context.
    """

    GWS_CLI_CONFIG_DIR = Path.home() / ".gws"
    GWS_CLI_CREDENTIALS_FILE = GWS_CLI_CONFIG_DIR / "credentials.json"

    # ------------------------------------------------------------------ #
    #  Credential storage (per-domain)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_all_credentials() -> dict:
        """Load the full credentials file as a dict keyed by domain."""
        if not CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.exists():
            return {}
        try:
            data = json.loads(
                CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.read_text(encoding="utf-8")
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
        CommunityCredentialService.GWS_CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.write_text(
            json.dumps({"credentials": credentials}, indent=2), encoding="utf-8"
        )
        CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.chmod(0o600)

    @staticmethod
    def get_current_api_domain() -> str:
        """Return the community API URL that is currently configured."""
        try:
            return Settings.get_community_api_url_and_check()
        except Exception:
            return "https://api.constellab.community"

    @staticmethod
    def get_community_front_url() -> str:
        """Get the community front URL."""
        return Settings.get_community_front_url_and_check()

    @staticmethod
    def get_community_api_url() -> str:
        """Get the community API URL."""
        return Settings.get_community_api_url_and_check()

    @staticmethod
    def save_credentials(access_token: str, expires_at: float | None = None,
                         domain: str | None = None) -> None:
        """Save access token for a given domain."""
        if domain is None:
            domain = CommunityCredentialService.get_current_api_domain()
        all_creds = CommunityCredentialService._load_all_credentials()
        entry: dict = {"access_token": access_token}
        if expires_at is not None:
            entry["expires_at"] = expires_at
        all_creds[domain] = entry
        CommunityCredentialService._save_all_credentials(all_creds)

    @staticmethod
    def load_credentials(domain: str | None = None) -> tuple[str | None, float | None]:
        """Load access token and expiration for the given (or current) domain.

        :return: Tuple of (access_token, expires_at) or (None, None)
        """
        if domain is None:
            domain = CommunityCredentialService.get_current_api_domain()
        all_creds = CommunityCredentialService._load_all_credentials()
        entry = all_creds.get(domain)
        if entry is None:
            return None, None
        return entry.get("access_token"), entry.get("expires_at")

    @staticmethod
    def load_access_token(domain: str | None = None) -> str | None:
        """Load a valid (non-expired) access token for the given domain."""
        access_token, expires_at = CommunityCredentialService.load_credentials(domain)
        if access_token is None:
            return None
        if expires_at is not None and time.time() >= expires_at:
            return None
        return access_token

    @staticmethod
    def delete_credentials(domain: str | None = None) -> None:
        """Delete credentials for a specific domain."""
        if domain is None:
            domain = CommunityCredentialService.get_current_api_domain()
        all_creds = CommunityCredentialService._load_all_credentials()
        if domain in all_creds:
            del all_creds[domain]
            CommunityCredentialService._save_all_credentials(all_creds)

    @staticmethod
    def delete_all_credentials() -> None:
        """Delete credentials for all domains."""
        if CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.exists():
            CommunityCredentialService.GWS_CLI_CREDENTIALS_FILE.unlink()

    @staticmethod
    def has_credentials(domain: str | None = None) -> bool:
        """Check if valid (non-expired) credentials exist for the domain."""
        return CommunityCredentialService.load_access_token(domain) is not None

    @staticmethod
    def is_token_expired(domain: str | None = None) -> bool:
        """Check if a token exists but is expired."""
        access_token, expires_at = CommunityCredentialService.load_credentials(domain)
        if access_token is None:
            return False
        if expires_at is None:
            return False
        return time.time() >= expires_at

    @staticmethod
    def get_stored_domains() -> list[str]:
        """Return all domains that have stored credentials."""
        return list(CommunityCredentialService._load_all_credentials().keys())


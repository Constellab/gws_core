import json
from pathlib import Path

from gws_core.community.community_user_service import CommunityUserService


class CommunityCliService:
    GWS_CLI_CONFIG_DIR = Path.home() / ".gws"
    GWS_CLI_CREDENTIALS_FILE = GWS_CLI_CONFIG_DIR / "credentials.json"

    @staticmethod
    def save_credentials(jwt_token: str) -> None:
        """Save JWT token to the credentials file."""
        CommunityCliService.GWS_CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        credentials = {"jwt_token": jwt_token}
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.write_text(
            json.dumps(credentials, indent=2), encoding="utf-8"
        )
        # Restrict file permissions to owner only
        CommunityCliService.GWS_CLI_CREDENTIALS_FILE.chmod(0o600)

    @staticmethod
    def load_jwt_token() -> str | None:
        """Load JWT token from the credentials file."""
        if not CommunityCliService.GWS_CLI_CREDENTIALS_FILE.exists():
            return None
        credentials = json.loads(
            CommunityCliService.GWS_CLI_CREDENTIALS_FILE.read_text(encoding="utf-8")
        )
        return credentials.get("jwt_token")

    @staticmethod
    def get_community_service(requires_authentication: bool = False) -> CommunityUserService:
        """Create a CommunityUserService with the stored JWT token.

        :param requires_authentication: If True, raise an error when no JWT token is found.
        """
        jwt_token = CommunityCliService.load_jwt_token()
        if requires_authentication and not jwt_token:
            raise Exception(
                "You are not authenticated. Please run 'gws community login <JWT_TOKEN>' first."
            )
        return CommunityUserService(jwt_token=jwt_token)

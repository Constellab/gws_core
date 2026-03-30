from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException

from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..impl.rich_text.rich_text_types import RichTextDTO
from .community_credential_service import CommunityCredentialService
from .community_dto import (
    CommunityDocumentationDTO,
    CommunityRagflowAskResponseDTO,
)


class TokenExpiredError(Exception):
    pass


class CommunityUserApiService:
    """Service for user-authenticated community API calls.

    Authenticates using a Bearer token (user access token).
    Used from CLI/MCP for documentation, chatbot, and brick publishing operations.
    """

    _access_token: str | None

    def __init__(self, requires_authentication: bool = False):
        """Initialize the service.

        :param requires_authentication: If True and no access_token is provided,
            load the token from stored credentials and raise if unavailable or expired.
        """
        if requires_authentication:
            domain = CommunityCredentialService.get_current_api_domain()
            self._access_token = CommunityCredentialService.load_access_token(domain)
            if not self._access_token:
                if CommunityCredentialService.is_token_expired(domain):
                    raise TokenExpiredError(
                        "Your session has expired. Please run 'gws community login' to re-authenticate."
                    )
                raise Exception(
                    "You are not authenticated. Please run 'gws community login' first."
                )
        else:
            self._access_token = None

    def ask_ragflow_chatbot(
        self, message: str, session_id: str | None = None
    ) -> CommunityRagflowAskResponseDTO:
        """Ask a question to the ragflow chatbot."""
        url = f"{self.get_community_api_url()}/ragflow-chatbot/ask"

        payload: dict = {"message": message}
        if session_id is not None:
            payload["sessionId"] = session_id

        try:
            response = ExternalApiService.post(
                url,
                payload,
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
                timeout=120,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't ask the ragflow chatbot. Error : {err.detail}"
            raise err

        data = response.json()
        return CommunityRagflowAskResponseDTO(
            answer=data.get("answer", ""),
            session_id=data.get("sessionId", ""),
            references=data.get("references", []),
        )

    def get_documentation(self, documentation_id: str) -> CommunityDocumentationDTO:
        """Retrieve a documentation page by its ID."""
        url = f"{self.get_community_api_url()}/documentation/{documentation_id}"

        try:
            response = ExternalApiService.get(
                url, headers=self._get_request_headers(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve documentation. Error : {err.detail}"
            raise err

        return CommunityDocumentationDTO.from_json(response.json())

    def update_documentation_content(
        self, documentation_id: str, content: RichTextDTO
    ) -> CommunityDocumentationDTO:
        """Update the content of a documentation page."""
        url = f"{self.get_community_api_url()}/documentation/content/{documentation_id}"

        try:
            response = ExternalApiService.put(
                url,
                content.to_json_dict(),
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't update documentation content. Error : {err.detail}"
            raise err

        return CommunityDocumentationDTO.from_json(response.json())

    def create_new_brick_version(self, brick_settings: BrickSettings) -> BrickSettings:
        """Create a new brick version on the community."""
        url = f"{self.get_community_api_url()}/brick/version-from-settings"

        try:
            response = ExternalApiService.post(
                url,
                brick_settings.to_json_dict(),
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create new brick version. Error : {err.detail}"
            raise err

        return BrickSettings.from_json_dict(response.json())

    @classmethod
    def get_community_api_url(cls) -> str:
        # return "https://community-api-pre-prod.constellab-pre-prod.gencovery.com"
        # return "https://api.constellab.community"
        return Settings.get_community_api_url_and_check()

    def _get_request_headers(self) -> dict[str, str]:
        """Return the headers for a request to the community API, with the Bearer token if provided."""
        headers: dict[str, str] = {}

        if self._access_token is not None:
            headers["Authorization"] = f"{self._access_token}"

        return headers

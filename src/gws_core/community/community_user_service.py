from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException

from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..impl.rich_text.rich_text_types import RichTextDTO
from .community_dto import (
    CommunityDocumentationDTO,
    CommunityRagflowAskResponseDTO,
)


class CommunityUserService:
    """Service to make requests to the community API using the user JWT for authentication"""

    jws_cookie_key: str = "Authorization"

    _jwt_token: str | None

    def __init__(self, jwt_token: str | None = None):
        self._jwt_token = jwt_token

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
                cookies=self._get_request_cookies(),
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
                url, cookies=self._get_request_cookies(), raise_exception_if_error=True
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
                cookies=self._get_request_cookies(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't update documentation content. Error : {err.detail}"
            raise err

        return CommunityDocumentationDTO.from_json(response.json())

    def create_new_brick_version(self, brick_settings: BrickSettings) -> BrickSettings:
        """Create a new brick version on the community."""
        url = f"{self.get_community_api_url()}/brick/new-version"

        try:
            response = ExternalApiService.post(
                url,
                brick_settings.to_json_dict(),
                cookies=self._get_request_cookies(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create new brick version. Error : {err.detail}"
            raise err

        return BrickSettings.from_json_dict(response.json())

    @classmethod
    def get_community_api_url(cls) -> str:
        # return "https://community-api-pre-prod.constellab-pre-prod.gencovery.com"
        community_api_url = Settings.get_community_api_url()
        if community_api_url is None:
            raise Exception("Environment variable 'COMMUNITY_API_URL' is not set")
        return community_api_url

    def _get_request_cookies(self) -> dict[str, str]:
        """
        Return the cookies for a request to the community API, with the JWT token if provided
        """
        cookies: dict[str, str] = {}

        if self._jwt_token is not None:
            cookies[self.jws_cookie_key] = self._jwt_token

        return cookies

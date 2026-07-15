from gws_core.brick.brick_settings import BrickSettings
from gws_core.brick.technical_doc_dto import TechnicalDocDTO
from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException

from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..impl.rich_text.rich_text_types import RichTextDTO
from .community_dto import (
    CommunityCreateDocResponseDTO,
    CommunityDocumentationDTO,
    CommunityRagflowAskResponseDTO,
    HnNode,
)


class CommunityUserService:
    """Service to make requests to the community API using a Bearer access token for authentication"""

    _access_token: str | None

    def __init__(self, access_token: str | None = None):
        self._access_token = access_token

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

    def get_documentation_hierarchy(self, brick_id: str, brick_version: str = "latest") -> HnNode:
        """Retrieve the documentation hierarchy (tree of folders and pages) of a brick.

        :param brick_id: ID of the brick whose documentation hierarchy to retrieve.
        :param brick_version: Brick version to retrieve the hierarchy for. Defaults to ``latest``.
        :return: The root node of the documentation hierarchy tree.
        """
        url = f"{self.get_community_api_url()}/brick/docs/{brick_id}/{brick_version}"

        try:
            response = ExternalApiService.get(
                url, headers=self._get_request_headers(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve documentation hierarchy. Error : {err.detail}"
            raise err

        return HnNode.from_json(response.json())

    def create_documentation(self, folder_id: str, title: str) -> CommunityCreateDocResponseDTO:
        """Create a new empty documentation page inside a folder.

        The freshly created page has no content yet; use the returned ``id`` with
        :meth:`update_documentation_content` to push content.

        :param folder_id: ID of the folder the documentation will be created in.
        :param title: Title of the new documentation page.
        :return: The created documentation page.
        """
        url = f"{self.get_community_api_url()}/folder/doc"

        payload = {
            "folderId": folder_id,
            "title": title,
            "type": "DOC",
        }

        try:
            response = ExternalApiService.post(
                url,
                payload,
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create documentation. Error : {err.detail}"
            raise err

        return CommunityCreateDocResponseDTO.from_json(response.json())

    def create_folder(self, folder_id: str, title: str) -> dict:
        """Create a new folder inside a folder.

        :param folder_id: ID of the parent folder the new folder will be created in.
        :param title: Title of the new folder.
        :return: The raw JSON payload returned by the API (contains at least the new folder's ``id``).
        """
        url = f"{self.get_community_api_url()}/folder"

        payload = {
            "id": None,
            "folderId": folder_id,
            "title": title,
            "type": "FOL",
        }

        try:
            response = ExternalApiService.post(
                url,
                payload,
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create folder. Error : {err.detail}"
            raise err

        return response.json()

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

    def create_technical_doc(self, brick_name: str, technical_doc: TechnicalDocDTO) -> None:
        """Push the technical documentation of a brick to the community."""
        url = f"{self.get_community_api_url()}/brick/create-technical-doc"

        payload = {
            "brickName": brick_name,
            "importFile": technical_doc.to_json_dict(),
        }

        try:
            ExternalApiService.post(
                url,
                payload,
                headers=self._get_request_headers(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't push technical documentation. Error : {err.detail}"
            raise err

    @classmethod
    def get_community_api_url(cls) -> str:
        return Settings.get_community_api_url_and_check()

    def _get_request_headers(self) -> dict[str, str]:
        """Return the headers for a request to the community API, with the Bearer token if provided."""
        headers: dict[str, str] = {}

        if self._access_token is not None:
            headers["Authorization"] = f"{self._access_token}"

        return headers

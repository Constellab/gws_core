from requests.models import Response

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_auth import ExternalLabAuth
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO,
    ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO,
    ExternalLabWithUserInfo,
    MarkEntityAsSharedDTO,
)
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.share.shared_dto import ShareLinkEntityType, ShareScenarioInfoReponseDTO
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class ExternalLabApiService:
    """Service to communicate with external lab API.

    Instance methods require a LabDTOWithCredentials and user_id,
    set via the constructor. Class methods are stateless utilities.
    """

    _lab_dto: LabDTOWithCredentials
    _user_id: str

    def __init__(self, lab_dto: LabDTOWithCredentials, user_id: str | None = None) -> None:
        if lab_dto.credentials_data is None:
            raise BadRequestException(
                GWSException.LAB_MISSING_CREDENTIALS_OR_DOMAIN.value, {"lab_name": lab_dto.name}
            )
        self._lab_dto = lab_dto
        if user_id is None:
            user_id = CurrentUserService.get_and_check_current_user().id
        self._user_id = user_id

    def send_resource_to_lab(
        self, request_dto: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Send a resource to the lab"""

        headers = self._get_auth_headers()

        url = self.get_full_route("resource/import")

        response = ExternalApiService.post(
            url, body=request_dto.to_json_dict(), headers=headers, raise_exception_if_error=True
        )

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    def get_imported_resource_from_scenario(
        self, scenario_id: str
    ) -> ExternalLabImportResourceResponseDTO:
        """Get the imported resource from the import scenario"""
        headers = self._get_auth_headers()

        url = self.get_full_route(f"resource/from-scenario/{scenario_id}")

        response = ExternalApiService.get(url, headers=headers, raise_exception_if_error=True)

        return ExternalLabImportResourceResponseDTO.from_json(response.json())

    def send_scenario_to_lab(
        self, request_dto: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Send a scenario to the lab"""

        headers = self._get_auth_headers()

        url = self.get_full_route("scenario/import")

        response = ExternalApiService.post(
            url, body=request_dto.to_json_dict(), headers=headers, raise_exception_if_error=True
        )

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    def get_scenario(self, id_: str) -> ExternalLabImportScenarioResponseDTO:
        """Get the scenario that is currently being imported"""
        headers = self._get_auth_headers()

        url = self.get_full_route(f"scenario/{id_}")

        response = ExternalApiService.get(url, headers=headers, raise_exception_if_error=True)

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    def get_scenario_export_info(self, scenario_id: str) -> ShareScenarioInfoReponseDTO:
        """Get scenario export info from an external lab using credentials."""
        headers = self._get_auth_headers()

        url = self.get_full_route(f"scenario/{scenario_id}/export-info")

        response = ExternalApiService.get(url, headers=headers, raise_exception_if_error=True)

        return ShareScenarioInfoReponseDTO.from_json(response.json())

    def get_resource_zip_route(self, resource_id: str) -> str:
        """Get the full URL for the resource zip endpoint on the external lab."""
        return self.get_full_route(f"resource/{resource_id}/zip")

    def get_full_route(self, route: str) -> str:
        """Get the full route for an external lab API call.

        Builds the URL from the lab's domain and mode.
        """
        if Settings.get_instance().is_test:
            return f"http://localhost:3000/{Settings.external_lab_api_route_path()}/{route}"
        api_url = self._lab_dto.get_api_url()
        return f"{api_url}/{Settings.external_lab_api_route_path()}/{route}"

    def _get_auth_headers(self) -> dict:
        """Get the external lab auth headers"""
        return ExternalLabAuth.get_auth_headers(
            self._lab_dto.credentials_data.api_key, self._user_id
        )

    ######################## CLASS METHODS #########################

    @classmethod
    def mark_shared_object_as_received(
        cls,
        lab_api_url: str,
        entity_type: ShareLinkEntityType,
        token: str,
        current_lab_info: ExternalLabWithUserInfo,
        external_id: str,
    ) -> Response:
        """Method that mark a shared object as received"""
        body = MarkEntityAsSharedDTO(lab_info=current_lab_info, external_id=external_id)
        return ExternalApiService.post(
            f"{lab_api_url}/{Settings.core_api_route_path()}/share/{entity_type.value}/mark-as-shared/{token}",
            body.to_json_dict(),
        )

    @classmethod
    def get_current_lab_info(cls, user: User) -> ExternalLabWithUserInfo:
        """Get information about the current lab. Useful when 2 labs communicate with each other."""
        lab = LabModel.get_or_create_current_lab()
        return ExternalLabWithUserInfo(
            lab=lab.to_dto(),
            lab_api_url=Settings.get_instance().get_lab_api_url(),
            user=user.to_dto(),
        )

    @classmethod
    def get_current_lab_route(cls, route: str) -> str:
        """Get the current lab route"""
        return f"{Settings.get_instance().get_lab_api_url()}/{route}"

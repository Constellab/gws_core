

from requests.models import Response

from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_type import CredentialsDataLab
from gws_core.external_lab.external_lab_auth import ExternalLabAuth
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO, ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO, ExternalLabWithUserInfo)
from gws_core.share.shared_dto import ShareLinkType
from gws_core.user.user import User


class ExternalLabApiService():
    """Class that contains method to communicate with external lab API"""

    @classmethod
    def mark_shared_object_as_received(cls, lab_api_url: str, entity_type: ShareLinkType,
                                       token: str, current_lab_info: ExternalLabWithUserInfo) -> Response:
        """Method that mark a shared object as received"""
        return ExternalApiService.post(
            f"{lab_api_url}/{Settings.core_api_route_path()}/share/{entity_type.value}/mark-as-shared/{token}",
            current_lab_info.to_json_dict())

    @classmethod
    def send_resource_to_lab(cls, request_dto: ExternalLabImportRequestDTO,
                             credentials: CredentialsDataLab, user_id: str) -> ExternalLabImportScenarioResponseDTO:
        """Send a resource to the lab"""

        headers = ExternalLabApiService._get_external_lab_auth(credentials.api_key, user_id)

        url = cls.get_full_route(credentials, "resource/import")

        response = ExternalApiService.post(url, body=request_dto.to_json_dict(), headers=headers,
                                           raise_exception_if_error=True)

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    @classmethod
    def get_imported_resource_from_scenario(cls, scenario_id: str, credentials: CredentialsDataLab, user_id: str) -> ExternalLabImportResourceResponseDTO:
        """Get the imported resource from the import scenario"""
        headers = ExternalLabApiService._get_external_lab_auth(credentials.api_key, user_id)

        url = cls.get_full_route(credentials, f"resource/from-scenario/{scenario_id}")

        response = ExternalApiService.get(url, headers=headers, raise_exception_if_error=True)

        return ExternalLabImportResourceResponseDTO.from_json(response.json())

    @classmethod
    def send_scenario_to_lab(cls, request_dto: ExternalLabImportRequestDTO,
                             credentials: CredentialsDataLab, user_id: str) -> ExternalLabImportScenarioResponseDTO:
        """Send a scenario to the lab"""

        headers = ExternalLabApiService._get_external_lab_auth(credentials.api_key, user_id)

        url = cls.get_full_route(credentials, "scenario/import")

        response = ExternalApiService.post(url, body=request_dto.to_json_dict(), headers=headers,
                                           raise_exception_if_error=True)

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    @classmethod
    def get_scenario(cls, id_: str, credentials: CredentialsDataLab, user_id: str) -> ExternalLabImportScenarioResponseDTO:
        """Get the scenario that is currently being imported"""
        headers = ExternalLabApiService._get_external_lab_auth(credentials.api_key, user_id)

        url = cls.get_full_route(credentials, f"scenario/{id_}")

        response = ExternalApiService.get(url, headers=headers, raise_exception_if_error=True)

        return ExternalLabImportScenarioResponseDTO.from_json(response.json())

    @classmethod
    def get_full_route(cls, credentials: CredentialsDataLab, route: str) -> str:
        """Get the full route"""
        if Settings.is_test:
            return f"http://localhost:3000/{Settings.external_lab_api_route_path()}/{route}"
        # for test purpose
        # return f"http://localhost:3000/{Settings.external_lab_api_route_path()}/{route}"
        return f"{credentials.get_lab_api_url()}/{Settings.external_lab_api_route_path()}/{route}"

    @classmethod
    def get_current_lab_info(cls, user: User) -> ExternalLabWithUserInfo:
        """Get information about the current lab. Usefule when 2 labs communicate with each other"""
        settings = Settings.get_instance()
        space = settings.get_space()
        return ExternalLabWithUserInfo(
            lab_id=settings.get_lab_id(),
            lab_name=settings.get_lab_name(),
            lab_api_url=settings.get_lab_api_url(),
            user_id=user.id,
            user_firstname=user.first_name,
            user_lastname=user.last_name,
            space_id=space['id'] if space is not None else None,
            space_name=space['name'] if space is not None else None
        )

    @classmethod
    def _get_external_lab_auth(cls, api_key: str, user_id: str) -> dict:
        """Get the external lab auth"""
        return ExternalLabAuth.get_auth_headers(api_key, user_id)

    @classmethod
    def get_current_lab_route(cls, route: str) -> str:
        """Get the current lab route"""
        return f"{Settings.get_instance().get_lab_api_url()}/{Settings.core_api_route_path()}/{route}"

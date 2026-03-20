from fastapi.responses import FileResponse

from gws_core.core.exception.exceptions.unauthorized_exception import UnauthorizedException
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO,
    ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO,
)
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.lab_model.lab_dto import LabDTO
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_transfert_service import ResourceTransfertService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_transfert_service import ScenarioTransfertService
from gws_core.share.share_service import ShareService
from gws_core.share.shared_dto import (
    ShareLinkEntityType,
    ShareResourceZippedResponseDTO,
    ShareScenarioInfoReponseDTO,
)
from gws_core.user.auth_context import AuthContextExternalLab
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user_dto import UserDTO
from gws_core.user.user_service import UserService


class ExternalLabService:
    @classmethod
    def import_resource(
        cls, import_resource: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Import resources from the lab.

        Resolves the source lab's LabModel from the auth context (set during
        API key authentication) and injects its PK into the params so
        ResourceDownloaderFromLab can authenticate back to the source.
        """
        params = import_resource.params

        auth_context = CurrentUserService.get_auth_context()
        if isinstance(auth_context, AuthContextExternalLab):
            params["lab"] = auth_context.get_lab().id
        else:
            raise UnauthorizedException("Invalid auth context, expected lab auth context")

        scenario = ResourceTransfertService.import_resource_from_lab_async(params)

        return cls._scenario_to_response_dto(scenario)

    @classmethod
    def get_imported_resource_from_scenario(
        cls, scenario_id: str
    ) -> ExternalLabImportResourceResponseDTO:
        """Get the imported resource from the scenario"""
        resource_model = ResourceTransfertService.get_imported_resource_from_scenario(scenario_id)
        return ExternalLabImportResourceResponseDTO(
            resource_model=resource_model.to_dto(),
            resource_url=FrontService().get_resource_url(resource_model.id),
            lab_info=ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            ),
        )

    @classmethod
    def import_scenario(
        cls, import_scenario: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Import scenario from the source lab.

        Resolves the source lab's LabModel from the auth context (set during
        API key authentication) and injects its PK into the params so
        ScenarioDownloaderFromLab can authenticate back to the source.
        """
        params = import_scenario.params

        auth_context = CurrentUserService.get_auth_context()
        if isinstance(auth_context, AuthContextExternalLab):
            params["lab"] = auth_context.get_lab().id
        else:
            raise UnauthorizedException("Invalid auth context, expected lab auth context")

        scenario = ScenarioTransfertService.import_from_lab_async(params)

        return cls._scenario_to_response_dto(scenario)

    @classmethod
    def stop_scenario(cls, id_: str) -> ExternalLabImportScenarioResponseDTO:
        """Stop a running scenario or remove it from queue."""
        proxy = ScenarioProxy.from_existing_scenario(id_)
        proxy.stop_or_remove_from_queue()

        return cls._scenario_to_response_dto(proxy.get_model())

    @classmethod
    def get_scenario(cls, id_: str) -> ExternalLabImportScenarioResponseDTO:
        """Get the scenario that is currently being imported"""
        scenario = Scenario.get_by_id_and_check(id_)
        return cls._scenario_to_response_dto(scenario)

    @classmethod
    def get_current_lab_info(cls) -> LabDTO:
        """Get information about the current lab from the LabModel table."""
        lab = LabModel.get_or_create_current_lab()
        return lab.to_dto()

    @classmethod
    def get_user_info(cls, user_id: str) -> UserDTO:
        """Get user info by id. If the user doesn't exist locally,
        import them from Constellab as inactive."""
        user = UserService.get_or_import_user_info(user_id)
        return user.to_dto()

    @classmethod
    def get_scenario_export_info(cls, scenario_id: str) -> ShareScenarioInfoReponseDTO:
        """Get scenario export info for credential-based downloading."""
        # verify scenario exists and is accessible before exporting it
        ScenarioService.get_by_id_and_check(scenario_id)

        export_package = ScenarioService.export_scenario(scenario_id)

        # Build resource route pointing to the credential-based zip endpoint
        resource_route = ExternalLabApiService.get_current_lab_route(
            f"{Settings.external_lab_api_route_path()}/resource/[RESOURCE_ID]/zip"
        )

        origin = ExternalLabApiService.get_current_lab_info(
            CurrentUserService.get_and_check_current_user()
        )

        return ShareScenarioInfoReponseDTO(
            version=ShareService.VERSION,
            entity_type=ShareLinkEntityType.SCENARIO,
            entity_id=scenario_id,
            entity_object=export_package,
            resource_route=resource_route,
            token="",
            origin=origin,
        )

    @classmethod
    def zip_resource(cls, resource_id: str) -> ShareResourceZippedResponseDTO:
        """Zip a resource for credential-based download."""
        ResourceModel.get_by_id_and_check(resource_id)

        current_user = CurrentUserService.get_and_check_current_user()
        zipped_resource = ShareService.zip_resource(resource_id, current_user)

        download_url = ExternalLabApiService.get_current_lab_route(
            f"{Settings.external_lab_api_route_path()}/resource/{resource_id}/download"
        )

        return ShareResourceZippedResponseDTO(
            version=ShareService.VERSION,
            entity_type=ShareLinkEntityType.RESOURCE,
            entity_id=resource_id,
            zipped_entity_resource_id=zipped_resource.id,
            download_entity_route=download_url,
        )

    @classmethod
    def download_resource(cls, resource_id: str) -> FileResponse:
        """Download a zipped resource using credentials."""

        zipped_resource = ShareService.find_existing_zipped_resource(resource_id)

        if not zipped_resource:
            raise Exception("The resource was not zipped")

        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception("Zip file is not a file")

        return FileHelper.create_file_response(zip_file.path)

    @classmethod
    def _scenario_to_response_dto(cls, scenario: Scenario) -> ExternalLabImportScenarioResponseDTO:
        return ExternalLabImportScenarioResponseDTO(
            scenario=scenario.to_dto(),
            scenario_url=FrontService().get_scenario_url(scenario.id),
            lab_info=ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            ),
            scenario_progress=scenario.get_current_progress(),
        )

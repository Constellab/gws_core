

from gws_core.core.service.front_service import FrontService
from gws_core.external_lab.external_lab_api_service import \
    ExternalLabApiService
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO, ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO)
from gws_core.resource.resource_service import ResourceService
from gws_core.scenario.scenario_downloader_service import \
    ScenarioDownloaderService
from gws_core.user.current_user_service import CurrentUserService


class ExternalLabService:

    @classmethod
    def import_resource(
            cls, import_resource: ExternalLabImportRequestDTO) -> ExternalLabImportResourceResponseDTO:
        """Import resources from the lab
        """
        resource_model = ResourceService.import_resource_from_link(import_resource.params)

        return ExternalLabImportResourceResponseDTO(
            resource_model=resource_model.to_dto(),
            resource_url=FrontService.get_resource_url(resource_model.id),
            lab_info=ExternalLabApiService.get_current_lab_info(CurrentUserService.get_and_check_current_user())
        )

    @classmethod
    def import_scenario(
            cls, import_scenario: ExternalLabImportRequestDTO) -> ExternalLabImportScenarioResponseDTO:
        """Import resources from the lab
        """
        scenario = ScenarioDownloaderService.import_from_lab(import_scenario.params)

        return ExternalLabImportScenarioResponseDTO(
            scenario=scenario.to_dto(),
            scenario_url=FrontService.get_scenario_url(scenario.id),
            lab_info=ExternalLabApiService.get_current_lab_info(CurrentUserService.get_and_check_current_user())
        )

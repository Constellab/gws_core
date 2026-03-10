from gws_core.core.service.front_service import FrontService
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO,
    ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO,
)
from gws_core.lab.lab_dto import LabDTO
from gws_core.lab.lab_model import LabModel
from gws_core.resource.resource_transfert_service import ResourceTransfertService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_transfert_service import ScenarioTransfertService
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user_dto import UserDTO
from gws_core.user.user_service import UserService


class ExternalLabService:
    @classmethod
    def import_resource(
        cls, import_resource: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Import resources from the lab"""
        scenario = ResourceTransfertService.import_resource_from_link_async(import_resource.params)

        return cls._scenario_to_response_dto(scenario)

    @classmethod
    def get_imported_resource_from_scenario(
        cls, scenario_id: str
    ) -> ExternalLabImportResourceResponseDTO:
        """Get the imported resource from the scenario"""
        resource_model = ResourceTransfertService.get_imported_resource_from_scenario(scenario_id)
        return ExternalLabImportResourceResponseDTO(
            resource_model=resource_model.to_dto(),
            resource_url=FrontService.get_resource_url(resource_model.id),
            lab_info=ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            ),
        )

    @classmethod
    def import_scenario(
        cls, import_scenario: ExternalLabImportRequestDTO
    ) -> ExternalLabImportScenarioResponseDTO:
        """Import resources from the lab"""
        scenario = ScenarioTransfertService.import_from_lab_async(import_scenario.params)

        return cls._scenario_to_response_dto(scenario)

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
    def _scenario_to_response_dto(cls, scenario: Scenario) -> ExternalLabImportScenarioResponseDTO:
        return ExternalLabImportScenarioResponseDTO(
            scenario=scenario.to_dto(),
            scenario_url=FrontService.get_scenario_url(scenario.id),
            lab_info=ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            ),
            scenario_progress=scenario.get_current_progress(),
        )

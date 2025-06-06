

from typing import Dict, List, Optional

from fastapi import Depends

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.entity_navigator.entity_navigator_dto import ImpactResultDTO
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.scenario.scenario_transfert_service import \
    ScenarioTransfertService

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .queue_service import QueueService
from .scenario_dto import (RunningScenarioInfoDTO,
                           ScenarioCountByTitleResultDTO, ScenarioDTO,
                           ScenarioSaveDTO)
from .scenario_run_service import ScenarioRunService
from .scenario_service import ScenarioService

###################################### GET ###############################


@core_app.get("/scenario/running", tags=["Scenario"],
              summary="Get the list of running scenarios")
def get_the_list_of_running_scenarios(
        _=Depends(AuthService.check_user_access_token)) -> List[RunningScenarioInfoDTO]:
    """
    Retrieve a list of running scenarios.
    """

    return ScenarioService.get_running_scenarios()


@core_app.get("/scenario/{id_}", tags=["Scenario"], summary="Get a scenario")
def get_an_scenario(id_: str,
                    _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Retrieve a scenario

    - **id_**: the id_ of a scenario
    """

    return ScenarioService.get_by_id_and_check(id_).to_dto()


@core_app.post("/scenario/advanced-search", tags=["Scenario"], summary="Advanced search for scenario")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> PageDTO[ScenarioDTO]:
    """
    Advanced search on scenario
    """
    return ScenarioService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario/title/{title}/count", tags=["Scenario"], summary="Count scenario by title")
def count_by_title(title: str,
                   _=Depends(AuthService.check_user_access_token)) -> ScenarioCountByTitleResultDTO:
    return ScenarioCountByTitleResultDTO(count=ScenarioService.count_by_title(title))


@core_app.get("/scenario/search-title/{title}", tags=["Scenario"], summary="Search scenario by title")
def search_by_title(title: str,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> PageDTO[ScenarioDTO]:
    """
    Advanced search on scenario
    """
    return ScenarioService.search_by_title(title, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario/input-resource/{resource_id}", tags=["Scenario"],
              summary="Get the list of scenarios by input resource")
def get_by_input_resource(resource_id: str,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _=Depends(AuthService.check_user_access_token)) -> PageDTO[ScenarioDTO]:
    """
    Retrieve a list of scenarios by the input resource
    """

    return ScenarioService.get_next_scenarios_of_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_dto()


###################################### CREATE ################################

@core_app.post("/scenario", tags=["Scenario"], summary="Create a scenario")
def create_an_scenario(scenario: ScenarioSaveDTO,
                       _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Create a scenario.
    """

    return ScenarioService.create_scenario_from_dto(
        scenario).to_dto()

###################################### UPDATE  ################################


@core_app.put("/scenario/{id_}/validate/{folder_id}", tags=["Scenario"], summary="Validate a scenario")
def validate_an_scenario(id_: str,
                         folder_id: str = None,
                         _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Validate a protocol

    - **id_**: the id_ of the scenario
    """

    return ScenarioService.validate_scenario_by_id(id_, folder_id=folder_id).to_dto()


@core_app.put("/scenario/{id_}/title", tags=["Scenario"],
              summary="Update the title of a scenario")
def update_title(id_: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioService.update_scenario_title(id_, body["title"]).to_dto()


class UpdateFolder(BaseModelDTO):
    folder_id: Optional[str]


@core_app.put("/scenario/{id_}/folder", tags=["Scenario"], summary="Update the folder of a scenario")
def update_scenario_folder(id_: str,
                           folder: UpdateFolder,
                           _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Update the folder of a scenario

    - **id_**: the id_ of the scenario
    - **folder_id**: the id_ of the folder
    """

    return ScenarioService.update_scenario_folder(id_, folder.folder_id).to_dto()


@core_app.put("/scenario/{id_}/description", tags=["Scenario"], summary="Update a scenario's description")
def update_scenario_description(id_: str,
                                description: RichTextDTO,
                                _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Update a scenario's description
    """

    return ScenarioService.update_scenario_description(id_, description).to_dto()


@core_app.put("/scenario/{id_}/reset", tags=["Scenario"], summary="Reset a scenario")
def reset_an_scenario(id_: str,
                      _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return EntityNavigatorService.reset_scenario(id_).to_dto()


@core_app.get("/scenario/{id_}/reset/check-impact", tags=["Scenario"], summary="Check impact for scenario reset")
def check_impact_for_scenario_reset(id_: str,
                                    _=Depends(AuthService.check_user_access_token)) -> ImpactResultDTO:
    return EntityNavigatorService.check_impact_for_scenario_reset(id_).to_dto()


@core_app.put("/scenario/{id_}/sync-with-space", tags=["Scenario"],
              summary="Synchronise the scenario with the space")
def sync_with_space(id_: str,
                    _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioService.synchronize_with_space_by_id(id_).to_dto()

###################################### RUN ################################


@core_app.post("/scenario/{id_}/start", tags=["Scenario"], summary="Start a scenario")
def start_an_scenario(id_: str,
                      _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Start a scenario

    - **flow**: the flow object
    """

    return QueueService.add_scenario_to_queue(scenario_id=id_).to_dto()


@core_app.post("/scenario/{id_}/stop", tags=["Scenario"], summary="Stop a scenario")
def stop_an_scenario(id_: str,
                     _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    """
    Stop a scenario

    - **id_**: the scenario id_
    """

    return ScenarioRunService.stop_scenario(id_).to_dto()

################################### COPY ##############################


@core_app.put("/scenario/{id_}/clone", tags=["Scenario"], summary="Clone a scenario")
def clone_scenario(id_: str,
                   _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioService.clone_scenario(id_).to_dto()

################################### DELETE ##############################


@core_app.delete("/scenario/{id_}", tags=["Scenario"], summary="Delete a scenario")
def delete_scenario(id_: str,
                    _=Depends(AuthService.check_user_access_token)) -> None:
    return EntityNavigatorService.delete_scenario(id_)


################################### ARCHIVE ##############################
@core_app.put("/scenario/{id_}/archive", tags=["Scenario"], summary="Archive a scenario")
def archive(id_: str,
            _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioService.archive_scenario_by_id(id_).to_dto()


@core_app.put("/scenario/{id_}/unarchive", tags=["Scenario"], summary="Unarchive a scenario")
def unarchive(id_: str,
              _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioService.unarchive_scenario_by_id(id_).to_dto()


################################### INTERMEDIATE RESOURCES ##############################

@core_app.delete("/scenario/{id_}/intermediate-resources", tags=["Scenario"],
                 summary="Delete all intermediate resources of a scenario")
def delete_intermediate_resources(id_: str,
                                  _=Depends(AuthService.check_user_access_token)) -> None:
    return ScenarioService.delete_intermediate_resources(id_)

    ################################### CREATE SCENARIO FROM LINK ##############################


@core_app.post("/scenario/import-from-lab", tags=["Share"],
               summary="Import a scenario from another lab")
def import_from_lab(values: ConfigParamsDict,
                    _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioTransfertService.import_from_lab_sync(values).to_dto()


@core_app.get("/scenario/import-from-lab/config-specs", tags=["Share"],
              summary="Get config specs for importing a scenario from another lab")
def get_import_scenario_config_specs(_=Depends(AuthService.check_user_access_token)) -> Dict[str, ParamSpecDTO]:
    return ScenarioTransfertService.get_import_scenario_config_specs()


@core_app.post("/scenario/{id_}/export-to-lab", tags=["Share"],
               summary="Export a scenario to another lab")
def export_to_lab(id_: str,
                  values: ConfigParamsDict,
                  _=Depends(AuthService.check_user_access_token)) -> ScenarioDTO:
    return ScenarioTransfertService.export_scenario_to_lab(id_, values).to_dto()


@core_app.get("/scenario/export-to-lab/config-specs", tags=["Share"],
              summary="Get config specs for exporting a scenario to another lab")
def get_export_to_lab_config_specs(_=Depends(AuthService.check_user_access_token)) -> Dict[str, ParamSpecDTO]:
    return ScenarioTransfertService.get_export_scenario_to_lab_config_specs()

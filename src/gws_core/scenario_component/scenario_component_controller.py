

from typing import Optional

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core_controller import core_app
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.scenario_component.scenario_component_dto import \
    ScenarioComponentDTO
from gws_core.user.auth_service import AuthService

from .scenario_component_service import ScenarioComponentService


@core_app.get("/scenario-component/{id}", tags=["Scenario component"], summary="Get an component")
def get_by_id(id: str,
              _=Depends(AuthService.check_user_access_token)) -> ScenarioComponentDTO:

    return ScenarioComponentService.get_by_id_and_check(id=id).to_dto()


@core_app.get("/scenario-component/{id}/graph", tags=["Scenario component"],
              summary="Get the component data by id")
def get_scenario_component_graph(id: str,
                                 _=Depends(AuthService.check_user_access_token)) -> ProtocolGraphConfigDTO:

    return ScenarioComponentService.get_by_id_and_check(id=id).get_protocol_config_dto()


@core_app.post("/scenario-component/import-from-file", tags=["Fs node"],
               summary="Import a component from a file")
def upload_folder(file: UploadFile = FastAPIFile(...),
                  _=Depends(AuthService.check_user_access_token)) -> ScenarioComponentDTO:

    return ScenarioComponentService.create_from_file(file).to_dto()


class UpdateScenarioComponent(BaseModelDTO):
    name: Optional[str] = None
    description: Optional[dict] = None


@core_app.put("/scenario-component/{id}", tags=["Scenario component"], summary="Update component")
def update(id: str,
           update_scenario_component: UpdateScenarioComponent,
           _=Depends(AuthService.check_user_access_token)) -> ScenarioComponentDTO:
    return ScenarioComponentService.update(id=id, name=update_scenario_component.name,
                                           description=update_scenario_component.description).to_dto()


class UpdateScenarioComponentName(BaseModelDTO):
    name: str


@core_app.put("/scenario-component/{id}", tags=["Scenario component"], summary="Update component name")
def update_name(id: str,
                update_scenario_component: UpdateScenarioComponentName,
                _=Depends(AuthService.check_user_access_token)) -> ScenarioComponentDTO:
    return ScenarioComponentService.update_name(id=id, name=update_scenario_component.name).to_dto()


@core_app.delete("/scenario-component/{id}", tags=["Scenario component"], summary="Delete an component")
def delete_by_id(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:

    ScenarioComponentService.delete(id=id)


@core_app.post("/scenario-component/search", tags=["Scenario component"],
               summary="Advanced search for component")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[ScenarioComponentDTO]:
    """
    Advanced search on component
    """
    return ScenarioComponentService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario-component/search-name/{name}", tags=["Scenario component"],
              summary="Search for component by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[ScenarioComponentDTO]:
    return ScenarioComponentService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario-component/{id}/download", tags=["Scenario component"],
              summary="Download a component json")
def download_template(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    template = ScenarioComponentService.get_by_id_and_check(id)
    return ResponseHelper.create_file_response_from_str(
        template.to_export_dto().to_json_str(),
        template.name + '.json')

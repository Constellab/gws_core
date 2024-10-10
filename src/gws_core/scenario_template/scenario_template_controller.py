

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
from gws_core.scenario_template.scenario_template_dto import \
    ScenarioTemplateDTO
from gws_core.user.auth_service import AuthService

from .scenario_template_service import ScenarioTemplateService


@core_app.get("/scenario-template/{id}", tags=["Scenario template"], summary="Get an scenario template")
def get_by_id(id: str,
              _=Depends(AuthService.check_user_access_token)) -> ScenarioTemplateDTO:

    return ScenarioTemplateService.get_by_id_and_check(id=id).to_dto()


@core_app.get("/scenario-template/{id}/graph", tags=["Scenario template"],
              summary="Get the scenario template data by id")
def get_scenario_template_graph(id: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolGraphConfigDTO:

    return ScenarioTemplateService.get_by_id_and_check(id=id).get_protocol_config_dto()


@core_app.post("/scenario-template/import-from-file", tags=["Fs node"],
               summary="Import a scenario template from a file")
def upload_folder(file: UploadFile = FastAPIFile(...),
                  _=Depends(AuthService.check_user_access_token)) -> ScenarioTemplateDTO:

    return ScenarioTemplateService.create_from_file(file).to_dto()


class UpdateScenarioTemplate(BaseModelDTO):
    name: Optional[str] = None
    description: Optional[dict] = None


@core_app.put("/scenario-template/{id}", tags=["Scenario template"], summary="Update scenario template")
def update(id: str,
           update_scenario_template: UpdateScenarioTemplate,
           _=Depends(AuthService.check_user_access_token)) -> ScenarioTemplateDTO:
    return ScenarioTemplateService.update(id=id, name=update_scenario_template.name,
                                          description=update_scenario_template.description).to_dto()


class UpdateScenarioTemplateName(BaseModelDTO):
    name: str


@core_app.put("/scenario-template/{id}", tags=["Scenario template"], summary="Update scenario template name")
def update_name(id: str,
                update_scenario_template: UpdateScenarioTemplateName,
                _=Depends(AuthService.check_user_access_token)) -> ScenarioTemplateDTO:
    return ScenarioTemplateService.update_name(id=id, name=update_scenario_template.name).to_dto()


@core_app.delete("/scenario-template/{id}", tags=["Scenario template"], summary="Delete an scenario template")
def delete_by_id(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:

    ScenarioTemplateService.delete(id=id)


@core_app.post("/scenario-template/search", tags=["Scenario template"], summary="Advanced search for scenario template")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[ScenarioTemplateDTO]:
    """
    Advanced search on scenario template
    """
    return ScenarioTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario-template/search-name/{name}", tags=["Scenario template"],
              summary="Search for scenario template by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[ScenarioTemplateDTO]:
    return ScenarioTemplateService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.get("/scenario-template/{id}/download", tags=["Scenario template"],
              summary="Download a scenario template json")
def download_template(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    template = ScenarioTemplateService.get_by_id_and_check(id)
    return ResponseHelper.create_file_response_from_str(
        template.to_export_dto().to_json_str(),
        template.name + '.json')

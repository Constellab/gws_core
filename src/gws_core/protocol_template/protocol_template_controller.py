

from typing import Optional

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core_controller import core_app
from gws_core.protocol.protocol_dto import ProtocolConfigDTO
from gws_core.protocol_template.protocol_template_dto import \
    ProtocolTemplateDTO
from gws_core.user.auth_service import AuthService

from .protocol_template_service import ProtocolTemplateService


@core_app.get("/protocol-template/{id}", tags=["Protocol template"], summary="Get an protocol template")
def get_by_id(id: str,
              _=Depends(AuthService.check_user_access_token)) -> ProtocolTemplateDTO:

    return ProtocolTemplateService.get_by_id_and_check(id=id).to_dto()


@core_app.get("/protocol-template/{id}/graph", tags=["Protocol template"],
              summary="Get the protocol template data by id")
def get_protocol_template_graph(id: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolConfigDTO:

    return ProtocolTemplateService.get_by_id_and_check(id=id).get_protocol_config_dto()


@core_app.post("/protocol-template/import-from-file", tags=["Fs node"],
               summary="Import a protocol template from a file")
def upload_folder(file: UploadFile = FastAPIFile(...),
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolTemplateDTO:

    return ProtocolTemplateService.create_from_file(file).to_dto()


class UpdateProtocolTemplate(BaseModel):
    name: Optional[str] = None
    description: Optional[dict] = None


@core_app.put("/protocol-template/{id}", tags=["Protocol template"], summary="Update protocol template")
def update(id: str,
           update_protocol_template: UpdateProtocolTemplate,
           _=Depends(AuthService.check_user_access_token)) -> ProtocolTemplateDTO:
    return ProtocolTemplateService.update(id=id, name=update_protocol_template.name,
                                          description=update_protocol_template.description).to_dto()


class UpdateProtocolTemplateName(BaseModel):
    name: str


@core_app.put("/protocol-template/{id}", tags=["Protocol template"], summary="Update protocol template name")
def update_name(id: str,
                update_protocol_template: UpdateProtocolTemplateName,
                _=Depends(AuthService.check_user_access_token)) -> ProtocolTemplateDTO:
    return ProtocolTemplateService.update_name(id=id, name=update_protocol_template.name).to_dto()


@core_app.delete("/protocol-template/{id}", tags=["Protocol template"], summary="Delete an protocol template")
def delete_by_id(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:

    ProtocolTemplateService.delete(id=id)


@core_app.post("/protocol-template/search", tags=["Protocol template"], summary="Advanced search for protocol template")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[ProtocolTemplateDTO]:
    """
    Advanced search on protocol template
    """
    return ProtocolTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/protocol-template/search-name/{name}", tags=["Protocol template"],
              summary="Search for protocol template by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[ProtocolTemplateDTO]:
    return ProtocolTemplateService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.get("/protocol-template/{id}/download", tags=["Protocol template"],
              summary="Download a protocol template json")
def download_template(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    template = ProtocolTemplateService.get_by_id_and_check(id)
    return ResponseHelper.create_file_response_from_str(template.to_export_dto().json(), template.name + '.json')

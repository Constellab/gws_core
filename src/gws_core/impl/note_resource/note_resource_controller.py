

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.note_resource.note_resource_service import \
    NoteResourceService
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.auth_service import AuthService


@core_app.get("/note-resource/{id_}/resource/{filename}/file", tags=["Note resource"],
              summary="Get the file of an note resource")
def get_note_image(id_: str,
                   filename: str,
                   _=Depends(AuthService.check_user_access_token)) -> FileResponse:

    file_path = NoteResourceService.get_file_path(id_, filename)
    return FileHelper.create_file_response(file_path)


@core_app.post("/note-resource/{id_}/resource/{sub_resource_key}/views/{view_name}", tags=["Note resource"],
               summary="Call view on a resource of an note resource")
def call_note_view(id_: str,
                   sub_resource_key: str,
                   view_name: str,
                   view_config: dict,
                   _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:

    return NoteResourceService.call_view_method(id_, sub_resource_key, view_name, view_config)

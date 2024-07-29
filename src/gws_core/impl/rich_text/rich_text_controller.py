

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse

from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text_file_service import (
    RichTextFileService, RichTextUploadFileResultDTO,
    RichTextUploadImageResultDTO)
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.auth_service import AuthService

########################################### IMAGE ###########################################


@core_app.post("/rich-text/{object_type}/{object_id}/image", tags=["Report"], summary="Upload an image to a rich text")
def upload_image(object_type: RichTextObjectType,
                 object_id: str,
                 image: UploadFile = FastAPIFile(...),
                 _=Depends(AuthService.check_user_access_token)) -> RichTextUploadImageResultDTO:
    return RichTextFileService.upload_image(object_type, object_id, image)


@core_app.get("/rich-text/{object_type}/{object_id}/image/{filename}",
              tags=["Report"],
              summary="Get an image of a rich text")
def get_image(object_type: RichTextObjectType,
              object_id: str,
              filename: str,
              _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    file_path = RichTextFileService.get_figure_file_path(object_type, object_id, filename)
    return FileHelper.create_file_response(file_path, filename=filename)


########################################### FILE VIEW ###########################################

@core_app.get("/rich-text/{object_type}/{object_id}/file-view/{filename}",
              tags=["Report"],
              summary="Get a file view content")
def get_file_view(object_type: RichTextObjectType,
                  object_id: str,
                  filename: str,
                  _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:
    return RichTextFileService.get_file_view(object_type, object_id, filename)


########################################### FILE ###########################################
@core_app.post("/rich-text/{object_type}/{object_id}/file", tags=["Report"], summary="Upload a file to a rich text")
def upload_file(object_type: RichTextObjectType,
                object_id: str,
                file: UploadFile = FastAPIFile(...),
                _=Depends(AuthService.check_user_access_token)) -> RichTextUploadFileResultDTO:
    return RichTextFileService.upload_file(object_type, object_id, file)


@core_app.get(
    "/rich-text/{object_type}/{object_id}/file/{filename}", tags=["Report"],
    summary="Get a file of a rich text")
def get_file(object_type: RichTextObjectType,
             object_id: str,
             filename: str,
             _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    file_path = RichTextFileService.get_uploaded_file_path(object_type, object_id, filename)
    return FileHelper.create_file_response(file_path, filename=filename)

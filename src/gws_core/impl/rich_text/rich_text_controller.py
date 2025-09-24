

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse

from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text_file_service import (
    RichTextFileService, RichTextUploadFileResultDTO,
    RichTextUploadImageResultDTO)
from gws_core.impl.rich_text.rich_text_transcription_service import \
    RichTextTranscriptionService
from gws_core.impl.rich_text.rich_text_types import (RichTextDTO,
                                                     RichTextObjectType)
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.authorization_service import AuthorizationService

########################################### IMAGE ###########################################


@core_app.post(
    "/rich-text/{object_type}/{object_id}/image", tags=["Rich text"],
    summary="Upload an image to a rich text")
def upload_image(object_type: RichTextObjectType,
                 object_id: str,
                 image: UploadFile = FastAPIFile(...),
                 _=Depends(AuthorizationService.check_user_access_token)) -> RichTextUploadImageResultDTO:
    return RichTextFileService.upload_image(object_type, object_id, image)


@core_app.get("/rich-text/{object_type}/{object_id}/image/{filename}",
              tags=["Rich text"],
              summary="Get an image of a rich text")
def get_image(object_type: RichTextObjectType,
              object_id: str,
              filename: str,
              _=Depends(AuthorizationService.check_user_access_token)) -> FileResponse:
    file_path = RichTextFileService.get_figure_file_path(object_type, object_id, filename)
    return FileHelper.create_file_response(file_path, filename=filename)


########################################### FILE VIEW ###########################################

@core_app.get("/rich-text/{object_type}/{object_id}/file-view/{filename}",
              tags=["Rich text"],
              summary="Get a file view content")
def get_file_view(object_type: RichTextObjectType,
                  object_id: str,
                  filename: str,
                  _=Depends(AuthorizationService.check_user_access_token)) -> CallViewResultDTO:
    return RichTextFileService.get_file_view(object_type, object_id, filename)


########################################### FILE ###########################################
@core_app.post("/rich-text/{object_type}/{object_id}/file", tags=["Rich text"], summary="Upload a file to a rich text")
def upload_file(object_type: RichTextObjectType,
                object_id: str,
                file: UploadFile = FastAPIFile(...),
                _=Depends(AuthorizationService.check_user_access_token)) -> RichTextUploadFileResultDTO:
    return RichTextFileService.upload_file(object_type, object_id, file)


@core_app.get(
    "/rich-text/{object_type}/{object_id}/file/{filename}", tags=["Rich text"],
    summary="Get a file of a rich text")
def get_file(object_type: RichTextObjectType,
             object_id: str,
             filename: str,
             _=Depends(AuthorizationService.check_user_access_token)) -> FileResponse:
    file_path = RichTextFileService.get_uploaded_file_path(object_type, object_id, filename)
    return FileHelper.create_file_response(file_path, filename=filename)


@core_app.post(
    "/rich-text/transcribe-audio", tags=["Rich text"],
    summary="Transcribe audio file to rich text")
def transcribe_audio(file: UploadFile = FastAPIFile(...),
                     _=Depends(AuthorizationService.check_user_access_token)) -> RichTextDTO:
    """ Transcribe an audio file to a rich text
    """

    return RichTextTranscriptionService.transcribe_uploaded_audio_to_rich_text(file).to_dto()

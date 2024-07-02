

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse

from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text_file_service import (
    RichTextFileService, RichTextUploadImageResultDTO)
from gws_core.user.auth_service import AuthService


@core_app.post("/rich-text/image", tags=["Report"], summary="Upload an image to a rich text")
def upload_image(image: UploadFile = FastAPIFile(...),
                 _=Depends(AuthService.check_user_access_token)) -> RichTextUploadImageResultDTO:
    return RichTextFileService.upload_image(image)


@core_app.get("/rich-text/image/{filename}", tags=["Report"], summary="Get an image of a rich text")
def get_image(filename: str,
              _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    file_path = RichTextFileService.get_file_path(filename)
    return FileHelper.create_file_response(file_path, filename=filename)

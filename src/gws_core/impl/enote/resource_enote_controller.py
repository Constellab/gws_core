

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core_controller import core_app
from gws_core.impl.enote.resource_enote_service import ResourceENoteService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.user.auth_service import AuthService


@core_app.get("/resource-enote/{id_}/image/{filename}", tags=["ENote"],
              summary="Get the image of an enote resource")
def get_enote_image(id_: str,
                    filename: str,
                    _=Depends(AuthService.check_user_access_token)) -> FileResponse:

    file_path = ResourceENoteService.get_file_path(id_, filename)
    return FileHelper.create_file_response(file_path)

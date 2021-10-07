# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.core.classes.paginator import PaginatorDict

from ...core_app import core_app
from ...user.auth_service import AuthService
from ...user.user_dto import UserData
from .file_service import FileService


@core_app.post("/file/upload", tags=["Files"], summary="Upload a file or a list of files")
async def upload_a_file_or_list_of_files(files: List[UploadFile] = FastAPIFile(...),
                                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Upload files

    """

    file = await FileService.upload_files(files=files)
    return file.to_json()


@core_app.get("/file/{typing_name}/{uri}/download", tags=["Files"], summary="Download a file")
async def download_a_file(uri: str,
                          typing_name: str,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file

    - **type**: the type of the file to download
    - **uri**: the uri of the file to download
    """

    file_response = FileService.download_file(uri=uri)
    return file_response


@core_app.get("/file", tags=["Files"], summary="Get the list of files")
async def get_the_list_of_files(page: Optional[int] = 1,
                                number_of_items_per_page: Optional[int] = 20,
                                _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of experiments. The list is paginated.

    - **type**: the type of the file to search
    - **number_of_items_per_page**: the number of items per page (limited to 50) s
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    return FileService.fetch_file_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page).to_json()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Literal, Optional

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.core.classes.jsonable import ListJsonable
from gws_core.core.classes.paginator import PaginatorDict

from ...core_app import core_app
from ...user.auth_service import AuthService
from ...user.user_dto import UserData
from .fs_node_service import FsNodeService


@core_app.post("/fs-node/upload-files", tags=["Fs node"], summary="Upload files")
def upload_a_file_or_list_of_files(files: List[UploadFile] = FastAPIFile(...),
                                   typing_names: List[str] = None,
                                   _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a list of files

    :param files: list of files to upload, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    :param typingNames: list of typing names for the files, defaults to None
    :type typingNames: List[str], optional
    """

    result = FsNodeService.upload_files(files=files, typing_names=typing_names)
    return result.to_json()


@core_app.post("/fs-node/upload-folder", tags=["Fs node"], summary="Upload a folder")
def upload_folder(files: List[UploadFile] = FastAPIFile(...),
                  _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a folder

    :param files: list of files of folder, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    """

    result = FsNodeService.upload_folder(files=files)
    return result.to_json()


@core_app.get("/fs-node/{id}/get-download-url", tags=["Files"], summary="Get a unique url to download the file")
def get_download_file_url(id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> str:
    """
    Generate a unique url to download the file
    """
    return f'fs-node/download?unique_code={FsNodeService.generate_download_file_url(id=id)}'


@core_app.get("/fs-node/download", tags=["Files"], summary="Download a file")
def download_a_file(id=Depends(AuthService.check_unique_code)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return FsNodeService.download_file(id=id)


@core_app.get("/fs-node", tags=["Files"], summary="Get the list of files")
def get_the_list_of_files(page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of experiments. The list is paginated.

    - **type**: the type of the file to search
    - **number_of_items_per_page**: the number of items per page (limited to 50) s
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    return FsNodeService.fetch_file_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page).to_json()


@core_app.put("/fs-node/{id}/type/{resource_typing_name}", tags=["Files"], summary="Update file type")
def update_file_type(id: str,
                     resource_typing_name: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    """
    Update a file.
    """

    return FsNodeService.update_file_type(id, resource_typing_name).to_json()

############################# FILE TYPE ###########################


@core_app.get("/file-type", tags=["Files"], summary="Get the list of file types")
def get_the_list_of_file_types(_: UserData = Depends(AuthService.check_user_access_token)) -> List[Dict]:
    """
    Get the list of file types
    """
    return ListJsonable(FsNodeService.get_file_types()).to_json()
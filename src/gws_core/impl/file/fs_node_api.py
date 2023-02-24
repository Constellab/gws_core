# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from typing_extensions import TypedDict

from gws_core.core.classes.jsonable import ListJsonable
from gws_core.task.converter.converter_service import ConverterService

from ...core_app import core_app
from ...user.auth_service import AuthService
from ...user.user_dto import UserData
from .fs_node_service import FsNodeService


# TODO TO REMOVE
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


@core_app.post("/fs-node/upload-file", tags=["Fs node"], summary="Upload file")
def uplaod_file(file: UploadFile = FastAPIFile(...),
                typing_name: List[str] = None,
                _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a file

    :param files: file to upload, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    :param typingNames: typing_name of the file, defaults to None
    :type typingNames: List[str], optional
    """

    result = FsNodeService.upload_file(upload_file=file, typing_name=typing_name[0])
    return result.to_json()


@core_app.post("/fs-node/upload-folder/{folder_typing_name}", tags=["Fs node"], summary="Upload a folder")
def upload_folder(folder_typing_name: str,
                  files: List[UploadFile] = FastAPIFile(...),
                  _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a folder

    :param files: list of files of folder, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    """

    result = FsNodeService.upload_folder(folder_typing_name=folder_typing_name, files=files)
    return result.to_json()


@core_app.get("/fs-node/{id}/download", tags=["Files"], summary="Download a file")
def download_a_file(id: str,
                    _: UserData = Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return FsNodeService.download_file(id=id)

############################# FILE EXTRACTOR ###########################


class ExtractFileDTO(TypedDict):
    path: str
    fs_node_typing_name: str


@core_app.put("/fs-node/{id}/extract-file", tags=["Files"], summary="Extract a file from a folder")
def extract_file(id: str,
                 extract: ExtractFileDTO,
                 _: UserData = Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    result = ConverterService.call_file_extractor(
        folder_model_id=id, sub_path=extract["path"],
        fs_node_typing_name=extract["fs_node_typing_name"])
    return result.to_json()


############################# FILE TYPE ###########################


@core_app.get("/fs-node/file-type", tags=["Files"], summary="Get the list of file types")
def get_file_types_list(_: UserData = Depends(AuthService.check_user_access_token)) -> List[Dict]:
    """
    Get the list of file types
    """
    return ListJsonable(FsNodeService.get_file_types()).to_json()


@core_app.get("/fs-node/folder-type", tags=["Files"], summary="Get the list of folder types")
def get_folder_types_list(_: UserData = Depends(AuthService.check_user_access_token)) -> List[Dict]:
    """
    Get the list of folder types
    """
    return ListJsonable(FsNodeService.get_folder_types()).to_json()

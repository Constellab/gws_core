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
from .fs_node_service import FsNodeService


@core_app.post("/fs-node/upload-file", tags=["Fs node"], summary="Upload file")
def upload_file(file: UploadFile = FastAPIFile(...),
                typing_name: List[str] = None,
                _=Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a file

    :param files: file to upload, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    :param typingNames: typing_name of the file, defaults to None
    :type typingNames: List[str], optional
    """

    result = FsNodeService.upload_file(
        upload_file=file, typing_name=typing_name[0])
    return result.to_json()


@core_app.post("/fs-node/upload-folder/{folder_typing_name}", tags=["Fs node"], summary="Upload a folder")
def upload_folder(folder_typing_name: str,
                  files: List[UploadFile] = FastAPIFile(...),
                  _=Depends(AuthService.check_user_access_token)) -> dict:
    """ Upload a folder

    :param files: list of files of folder, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    """

    result = FsNodeService.upload_folder(
        folder_typing_name=folder_typing_name, files=files)
    return result.to_json()


@core_app.get("/fs-node/{id}/download", tags=["Files"], summary="Download a file")
def download_a_file(id: str,
                    _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return FsNodeService.download_file(fs_node_id=id)


############################# FOLDER ROUTES ###########################


class ExtractFileDTO(TypedDict):
    path: str
    fs_node_typing_name: str


@core_app.put("/fs-node/{id}/folder/extract-node", tags=["Files"], summary="Extract a node from a folder")
def extract_node_from_folder(id: str,
                             extract: ExtractFileDTO,
                             _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Extract a node from a folder to make it a new Resource
    """
    result = ConverterService.call_file_extractor(
        folder_model_id=id, sub_path=extract["path"],
        fs_node_typing_name=extract["fs_node_typing_name"])
    return result.to_json()


# make the node_path variable supports slashes and dots
@core_app.get("/fs-node/{id}/folder/download/{node_path:path}", tags=["Files"],
              summary="Download the node from a folder")
def download_fsnode_from_folder(id: str,
                                node_path: str,
                                _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download the node in a folder
    """
    return FsNodeService.download_fsnode_from_folder(folder_id=id, file_path=node_path)


class SubFilePath(TypedDict):
    sub_file_path: str


@core_app.post("/fs-node/{id}/folder/sub-file-view", tags=["Files"],
               summary="Call the default view of a folder sub file")
def call_folder_sub_file_view(id: str,
                              data: SubFilePath,
                              _=Depends(AuthService.check_user_access_token)):
    """
    Call the default view of a sub file in a folder
    """
    return FsNodeService.call_folder_sub_file_view(resource_id=id, sub_file_path=data['sub_file_path']).to_json()


############################# FILE TYPE ###########################


@core_app.get("/fs-node/file-type", tags=["Files"], summary="Get the list of file types")
def get_file_types_list(_=Depends(AuthService.check_user_access_token)) -> List[Dict]:
    """
    Get the list of file types
    """
    return ListJsonable(FsNodeService.get_file_types()).to_json()


@core_app.get("/fs-node/folder-type", tags=["Files"], summary="Get the list of folder types")
def get_folder_types_list(_=Depends(AuthService.check_user_access_token)) -> List[Dict]:
    """
    Get the list of folder types
    """
    return ListJsonable(FsNodeService.get_folder_types()).to_json()

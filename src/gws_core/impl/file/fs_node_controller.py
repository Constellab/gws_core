

from typing import List

from fastapi import Depends
from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.model.typing_dto import TypingDTO
from gws_core.resource.resource_dto import ResourceDTO
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.task.converter.converter_service import ConverterService

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .fs_node_service import FsNodeService


@core_app.post("/fs-node/upload-file", tags=["Fs node"], summary="Upload file")
def upload_file(file: UploadFile = FastAPIFile(...),
                typing_name: List[str] = None,
                _=Depends(AuthService.check_user_access_token)) -> ResourceDTO:
    """ Upload a file

    :param files: file to upload, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    :param typingNames: typing_name of the file, defaults to None
    :type typingNames: List[str], optional
    """

    return FsNodeService.upload_file(
        upload_file=file, typing_name=typing_name[0]).to_dto()
    return a


@core_app.post("/fs-node/upload-folder/{folder_typing_name}", tags=["Fs node"], summary="Upload a folder")
def upload_folder(folder_typing_name: str,
                  files: List[UploadFile] = FastAPIFile(...),
                  _=Depends(AuthService.check_user_access_token)) -> ResourceDTO:
    """ Upload a folder

    :param files: list of files of folder, defaults to FastAPIFile(...)
    :type files: List[UploadFile], optional
    """

    return FsNodeService.upload_folder(
        folder_typing_name=folder_typing_name, files=files).to_dto()


@core_app.get("/fs-node/{id}/download", tags=["Files"], summary="Download a file")
def download_a_file(id: str,
                    _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return FsNodeService.download_file(fs_node_id=id)


############################# FOLDER ROUTES ###########################


class ExtractFileDTO(BaseModelDTO):
    path: str
    fs_node_typing_name: str


@core_app.put("/fs-node/{id}/folder/extract-node", tags=["Files"], summary="Extract a node from a folder")
def extract_node_from_folder(id: str,
                             extract: ExtractFileDTO,
                             _=Depends(AuthService.check_user_access_token)) -> ResourceDTO:
    """
    Extract a node from a folder to make it a new Resource
    """
    return ConverterService.call_file_extractor(
        folder_model_id=id, sub_path=extract.path,
        fs_node_typing_name=extract.fs_node_typing_name).to_dto()


class SubFilePath(BaseModelDTO):
    sub_file_path: str


@core_app.post("/fs-node/{id}/folder/sub-file-view", tags=["Files"],
               summary="Call the default view of a folder sub file")
def call_folder_sub_file_view(id: str,
                              data: SubFilePath,
                              _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:
    """
    Call the default view of a sub file in a folder
    """
    return FsNodeService.call_folder_sub_file_view(resource_id=id, sub_file_path=data.sub_file_path).to_dto()


@core_app.post("/fs-node/{id}/folder/download-sub-node", tags=["Files"],
               summary="Download a sub file of a folder")
def download_folder_sub_file(id: str,
                             data: SubFilePath,
                             _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Call the default view of a sub file in a folder
    """
    return FsNodeService.download_folder_sub_node(resource_id=id, sub_file_path=data.sub_file_path)

############################# FILE TYPE ###########################


@core_app.get("/fs-node/file-type", tags=["Files"], summary="Get the list of file types")
def get_file_types_list(_=Depends(AuthService.check_user_access_token)) -> List[TypingDTO]:
    """
    Get the list of file types
    """
    typings = FsNodeService.get_file_types()
    return [typing.to_dto() for typing in typings]


@core_app.get("/fs-node/folder-type", tags=["Files"], summary="Get the list of folder types")
def get_folder_types_list(_=Depends(AuthService.check_user_access_token)) -> List[TypingDTO]:
    """
    Get the list of folder types
    """
    typings = FsNodeService.get_folder_types()
    return [typing.to_dto() for typing in typings]

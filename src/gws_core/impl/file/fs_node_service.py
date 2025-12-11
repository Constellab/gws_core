import os
import shutil
from pathlib import Path

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from typing_extensions import Buffer

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.utils import Utils
from gws_core.entity_navigator.entity_navigator import EntityNavigatorResource
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_result import CallViewResult

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from ...core.exception.exceptions.not_found_exception import NotFoundException
from ...model.typing_manager import TypingManager
from ...resource.resource_model import ResourceModel
from ...resource.resource_typing import FileTyping, ResourceTyping
from .file import File
from .file_helper import FileHelper
from .file_store import FileStore
from .folder import Folder
from .fs_node import FSNode
from .local_file_store import LocalFileStore


class FsNodeService:
    @classmethod
    def download_file(cls, fs_node_id: str) -> File:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(fs_node_id)
        resource = resource_model.get_resource()

        if not isinstance(resource, File):
            raise BadRequestException("Can't download resource because it is not an File")

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.node_path_exists(resource.path):
            raise NotFoundException("The file does not exists on the server. It has been deleted")

        return resource

    @classmethod
    def preview_file(cls, fs_node_id: str, file_name: str, resource_uid: str) -> File:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(fs_node_id)
        resource = resource_model.get_resource()

        if not isinstance(resource, File):
            raise BadRequestException("Can't preview resource because it is not an File")

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.node_path_exists(resource.path):
            raise NotFoundException("The file does not exists on the server. It has been deleted")

        # check if the filename and resource uid are valid
        if resource.get_name() != file_name or resource.uid != resource_uid:
            raise BadRequestException("The preview link is not valid")

        return resource

    ############################# UPLOAD / CREATION  ###########################

    @classmethod
    @GwsCoreDbManager.transaction()
    def upload_file(cls, upload_file: UploadFile, typing_name: str) -> ResourceModel:
        """Upload a file to the store and create the resource."""
        file_type: type[File] = TypingManager.get_and_check_type_from_name(typing_name)

        temp_dir = Settings.make_temp_dir()
        # create the file in the temp dir
        file_path = cls.create_tmp_file(
            upload_file.file, os.path.join(temp_dir, upload_file.filename)
        )

        file: File = file_type(file_path)

        try:
            # Call the check resource on file
            try:
                error = file.check_resource()
            except Exception as err:
                error = str(err)
                Logger.log_exception_stack_trace(err)
            if error is not None and error:
                raise BadRequestException(
                    GWSException.INVALID_FILE_ON_UPLOAD.value,
                    GWSException.INVALID_FILE_ON_UPLOAD.name,
                    {"error": error},
                )

            return cls.create_fs_node_model(file)
        finally:
            FileHelper.delete_dir(temp_dir)

    @classmethod
    def create_tmp_file(cls, upload_file: Buffer, file_path: str) -> str:
        # create parent dir if not exist
        FileHelper.create_dir_if_not_exist(FileHelper.get_dir(file_path))

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file, buffer)

        return file_path

    ############################# FS NODE  ###########################

    @classmethod
    def create_fs_node_model(cls, fs_node: FSNode) -> ResourceModel:
        return ResourceModel.save_from_resource(fs_node, origin=ResourceOrigin.UPLOADED)

    ############################# FOLDER ###########################

    @classmethod
    @GwsCoreDbManager.transaction()
    def upload_folder(
        cls, folder_typing_name: str, files: list[UploadFile] = FastAPIFile(...)
    ) -> ResourceModel:
        if len(files) == 0:
            raise BadRequestException("The folder is empty")

        folder_type: type[Folder] = TypingManager.get_and_check_type_from_name(folder_typing_name)

        if not Utils.issubclass(folder_type, Folder):
            raise BadRequestException("The type is not a sub class of Folder")

        temp_dir = Settings.make_temp_dir()

        try:
            # retrieve the folder name
            path: Path = FileHelper.get_path(files[0].filename)
            folder_name: str = path.parts[0]

            # Add all the file under the create folder
            for file in files:
                cls.create_tmp_file(file.file, os.path.join(temp_dir, file.filename))

            folder: Folder = folder_type(os.path.join(temp_dir, folder_name))
            try:
                # Call the check resource on the folder
                error = folder.check_resource()
            except Exception as err:
                error = str(err)
                Logger.log_exception_stack_trace(err)
            if error is not None and error:
                raise BadRequestException(
                    GWSException.INVALID_FOLDER_ON_UPLOAD.value,
                    GWSException.INVALID_FOLDER_ON_UPLOAD.name,
                    {"error": error},
                )

            return cls.create_fs_node_model(folder)
        finally:
            FileHelper.delete_dir(temp_dir)

    @classmethod
    def call_folder_sub_file_view(cls, resource_id: str, sub_file_path: str) -> CallViewResult:
        resource_model: ResourceModel = ResourceService.get_by_id_and_check(resource_id)

        view_name = Folder.view_sub_file.__name__

        return ResourceService.call_view_on_resource_model(
            resource_model=resource_model,
            view_name=view_name,
            config_values={"sub_file_path": sub_file_path},
            save_view_config=True,
        )

    @classmethod
    def download_folder_sub_node(cls, resource_id: str, sub_file_path: str) -> FileResponse:
        resource_model: ResourceModel = ResourceService.get_by_id_and_check(resource_id)
        resource: Folder = resource_model.get_resource()

        if not isinstance(resource, Folder):
            raise BadRequestException("Can't download resource because it is not an Folder")

        sub_path_full = resource.get_sub_path(sub_file_path)

        # for now, the direct download for a folder is not allowed
        if FileHelper.is_dir(sub_path_full):
            raise BadRequestException(
                "The direct download of sub folder is not yet supported. Please call 'Extract folder' on the sub folder, then download the extracted folder"
            )

        return FileHelper.create_file_response(
            sub_path_full, filename=FileHelper.get_name_without_extension(sub_file_path)
        )

    @classmethod
    def rename_folder_sub_node(cls, resource_id: str, sub_file_path: str, new_name: str) -> None:
        folder = cls._get_and_check_folder_before_modification(resource_id)

        folder.rename_sub_node(sub_file_path, new_name)

    @classmethod
    def delete_folder_sub_node(cls, resource_id: str, sub_file_path: str) -> None:
        folder = cls._get_and_check_folder_before_modification(resource_id)

        folder.delete_sub_node(sub_file_path)

    @classmethod
    def _get_and_check_folder_before_modification(cls, resource_id: str) -> Folder:
        resource_model: ResourceModel = ResourceService.get_by_id_and_check(resource_id)
        resource = resource_model.get_resource()

        if not isinstance(resource, Folder):
            raise BadRequestException("The resource is not a folder")

        resource_navigation = EntityNavigatorResource(resource_model)

        if resource_navigation.has_next_entities([NavigableEntityType.SCENARIO]):
            raise BadRequestException("The folder is used in a scenario, it can't be modified")

        return resource

    ############################# FILE TYPE ###########################

    @classmethod
    def get_file_types(cls) -> list[FileTyping]:
        return FileTyping.get_typings()

    @classmethod
    def get_folder_types(cls) -> list[ResourceTyping]:
        return ResourceTyping.get_folder_types()



import os
from pathlib import Path
from typing import List, Type

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse

from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_result import CallViewResult

from ...core.decorator.transaction import transaction
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.exception.exceptions.not_found_exception import NotFoundException
from ...core.service.base_service import BaseService
from ...model.typing_manager import TypingManager
from ...resource.resource_model import ResourceModel
from ...resource.resource_typing import FileTyping, ResourceTyping
from .file import File
from .file_helper import FileHelper
from .file_store import FileStore
from .folder import Folder
from .fs_node import FSNode
from .local_file_store import LocalFileStore


class FsNodeService(BaseService):

    @classmethod
    def download_file(cls, fs_node_id: str) -> FileResponse:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(fs_node_id)
        resource: File = resource_model.get_resource()

        if not isinstance(resource, File):
            raise BadRequestException(
                "Can't download resource because it is not an File")

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.node_path_exists(resource.path):
            raise NotFoundException(
                f"The file does not exists on the server. It has been deleted")

        return FileHelper.create_file_response(resource.path, filename=resource.get_default_name())

    ############################# UPLOAD / CREATION  ###########################

    @classmethod
    @transaction()
    def upload_file(cls, upload_file: UploadFile, typing_name: str) -> ResourceModel:
        """Upload a file to the store and create the resource.
        """

        file_store: FileStore = LocalFileStore.get_default_instance()
        file_type: Type[File] = TypingManager.get_type_from_name(typing_name)

        # retrieve the name of the file without the folder if there are some
        filename = FileHelper.get_name_with_extension(upload_file.filename)
        file: File = file_store.add_from_temp_file(
            upload_file.file, filename, file_type)

        # Call the check resource on file
        try:
            error = file.check_resource()
        except Exception as err:
            error = str(err)
            Logger.log_exception_stack_trace(err)
        if error is not None and len(error):
            file_store.delete_node(file)
            raise BadRequestException(GWSException.INVALID_FILE_ON_UPLOAD.value,
                                      GWSException.INVALID_FILE_ON_UPLOAD.name, {'error': error})

        return cls.create_fs_node_model(file)

    @classmethod
    def add_file_to_default_store(cls, file: File, dest_file_name: str = None) -> ResourceModel:
        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        return cls._add_file_to_store(file=file, store=file_store, dest_file_name=dest_file_name)

    @classmethod
    def add_file_to_store(cls, file: File, store_id: str, dest_file_name: str = None) -> ResourceModel:
        file_store: LocalFileStore = FileStore.get_by_id_and_check(store_id)
        return cls._add_file_to_store(file=file, store=file_store, dest_file_name=dest_file_name)

    @classmethod
    def _add_file_to_store(cls, file: File, store: FileStore, dest_file_name: str = None) -> ResourceModel:
        new_file: File = store.add_file_from_path(
            source_file_path=file.path, dest_file_name=dest_file_name)
        return cls.create_fs_node_model(new_file)

############################# FS NODE  ###########################

    @classmethod
    def create_fs_node_model(cls, fs_node: FSNode) -> ResourceModel:
        return ResourceModel.save_from_resource(fs_node, origin=ResourceOrigin.UPLOADED)


############################# FOLDER ###########################

    @classmethod
    @transaction()
    def upload_folder(cls, folder_typing_name: str, files: List[UploadFile] = FastAPIFile(...)) -> ResourceModel:
        if len(files) == 0:
            raise BadRequestException('The folder is empty')

        folder_type: Type[Folder] = TypingManager.get_type_from_name(
            folder_typing_name)

        if not Utils.issubclass(folder_type, Folder):
            raise BadRequestException('The type is not a sub class of Folder')

        # retrieve the folder name
        path: Path = FileHelper.get_path(files[0].filename)
        folder_name: str = path.parts[0]

        # create the folder
        file_store: FileStore = LocalFileStore.get_default_instance()
        folder_model: ResourceModel = cls.create_empty_folder(
            folder_name, file_store, folder_type)
        folder: Folder = folder_model.get_resource()

        # Add all the file under the create folder
        for file in files:
            file_path: Path = FileHelper.get_path(file.filename)
            # replace the initial folder name with the name of the generated folder
            new_file_path = os.path.join(
                folder.get_default_name(), *file_path.parts[1:])
            # use file.file to access temporary file
            file_store.add_from_temp_file(file.file, new_file_path)

        # Call the check resource on the folder
        try:
            error = folder.check_resource()
        except Exception as err:
            error = str(err)
            Logger.log_exception_stack_trace(err)
        if error is not None and len(error):
            file_store.delete_node(folder)
            raise BadRequestException(GWSException.INVALID_FOLDER_ON_UPLOAD.value,
                                      GWSException.INVALID_FOLDER_ON_UPLOAD.name, {'error': error})

        # Recalculate and set the folder size after all the files are set in folder
        folder_model.fs_node_model.size = folder.get_size()
        folder_model.fs_node_model.save()

        return folder_model

    @classmethod
    def create_empty_folder(cls, path: str, store: FileStore, folder_type: Type[Folder] = Folder) -> ResourceModel:
        folder = store.create_empty_folder(path, folder_type)
        return cls.create_fs_node_model(folder)

    @classmethod
    def call_folder_sub_file_view(cls, resource_id: str, sub_file_path: str) -> CallViewResult:
        resource_model: ResourceModel = ResourceService.get_by_id_and_check(
            resource_id)

        view_name = Folder.view_sub_file.__name__

        return ResourceService.call_view_on_resource_model(
            resource_model=resource_model, view_name=view_name, config_values={
                'sub_file_path': sub_file_path}, save_view_config=True)


############################# FILE TYPE ###########################

    @classmethod
    def get_file_types(cls) -> List[FileTyping]:
        return FileTyping.get_typings()

    @classmethod
    def get_folder_types(cls) -> List[ResourceTyping]:
        return ResourceTyping.get_folder_types()

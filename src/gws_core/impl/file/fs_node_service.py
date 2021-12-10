# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from pathlib import Path
from typing import List, Optional, Type

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse

from ...core.classes.jsonable import Jsonable, ListJsonable
from ...core.classes.paginator import Paginator
from ...core.decorator.transaction import transaction
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.exception.exceptions.not_found_exception import NotFoundException
from ...core.service.base_service import BaseService
from ...core.utils.utils import Utils
from ...model.typing_manager import TypingManager
from ...resource.resource import Resource
from ...resource.resource_model import ResourceModel, ResourceOrigin
from ...resource.resource_service import ResourceService
from ...resource.resource_typing import FileTyping
from ...user.current_user_service import CurrentUserService
from ...user.unique_code_service import UniqueCodeService
from .file import File
from .file_helper import FileHelper
from .file_store import FileStore
from .folder import Folder
from .fs_node import FSNode
from .local_file_store import LocalFileStore


class FsNodeService(BaseService):

    @classmethod
    def fetch_file_list(cls,
                        page: Optional[int] = 1,
                        number_of_items_per_page: Optional[int] = 20) -> Paginator:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = ResourceModel.select().where(
            (ResourceModel.origin == ResourceOrigin.IMPORTED) & (ResourceModel.fs_node_model is not None)).order_by(
            ResourceModel.created_at.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def generate_download_file_url(cls, id: str) -> str:
        return UniqueCodeService.generate_code(CurrentUserService.get_and_check_current_user().id, id)

    @classmethod
    def download_file(cls, id: str) -> FileResponse:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(id)
        resource: Resource = resource_model.get_resource()

        if not isinstance(resource, File):
            raise BadRequestException(f"The resource is not a file")

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.node_name_exists(resource.name):
            raise NotFoundException(f"The file '{resource.name}' does not exists on the server. It has been deleted")

        return FileResponse(resource.path, media_type='application/octet-stream', filename=resource.name)

    ############################# UPLOAD / CREATION  ###########################

    @classmethod
    def upload_files(cls, files: List[UploadFile] = FastAPIFile(...), typing_names: List[str] = None) -> Jsonable:
        """Upload multiple files to the serveur flat.
        """

        file_store: FileStore = LocalFileStore.get_default_instance()

        result: ListJsonable = ListJsonable()
        for index, file in enumerate(files):
            file_model: List[ResourceModel] = cls.upload_file_to_store(file, typing_names[index], file_store)
            result.append(file_model)

        return result

    @classmethod
    @transaction()
    def upload_file_to_store(cls, upload_file: UploadFile, typing_name: str, store: FileStore) -> List[ResourceModel]:
        """Upload a file to the store and create the resource. If the file path contains '/' or '\' it also create the folders and resource for the folders
        """
        resource_models: List[ResourceModel] = []

        file_type: Type[File] = TypingManager.get_type_from_name(typing_name)

        # retrieve the name of the file without the folder if there are some
        filename = FileHelper.get_name_with_extension(upload_file.filename)
        file: File = store.add_from_temp_file(upload_file.file, filename, file_type)

        resource_models.append(cls.create_fs_node_model(file))
        return resource_models

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
        new_file: File = store.add_file_from_path(source_file_path=file.path, dest_file_name=dest_file_name)
        return cls.create_fs_node_model(new_file)

    @classmethod
    def update_file_type(cls, file_id: str, file_typing_name: str) -> ResourceModel:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(file_id)

        ResourceService.check_before_resource_update(resource_model)

        file_type: Type[File] = TypingManager.get_type_from_name(file_typing_name)

        if not Utils.issubclass(file_type, File):
            raise BadRequestException('The type must be a File')

        resource_model.resource_typing_name = file_type._typing_name
        return resource_model.save()


############################# FS NODE  ###########################

    @classmethod
    def create_fs_node_model(cls, fs_node: FSNode) -> ResourceModel:
        return ResourceModel.save_from_resource(fs_node, origin=ResourceOrigin.IMPORTED)


############################# FOLDER ###########################


    @classmethod
    def upload_folder(cls, files: List[UploadFile] = FastAPIFile(...)) -> ResourceModel:
        if len(files) == 0:
            raise BadRequestException('The folder is empty')

        # retrieve the folder name
        path: Path = FileHelper.get_path(files[0].filename)
        folder_name: str = path.parts[0]

        # create the folder
        file_store: FileStore = LocalFileStore.get_default_instance()
        folder_model: ResourceModel = cls.create_empty_folder(folder_name, file_store)
        folder: Folder = folder_model.get_resource()

        # Add all the file under the create folder
        for file in files:
            file_path: Path = FileHelper.get_path(file.filename)
            # replace the initial folder name with the name of the generated folder
            new_file_path = os.path.join(folder.get_name(), *file_path.parts[1:])
            # use file.file to access temporary file
            file_store.add_from_temp_file(file.file, new_file_path)

        return folder_model

    @classmethod
    def create_empty_folder(cls, path: str, store: FileStore) -> ResourceModel:
        folder = store.create_empty_folder(path)
        return cls.create_fs_node_model(folder)

############################# FILE TYPE ###########################

    @classmethod
    def get_file_types(cls) -> List[FileTyping]:
        return FileTyping.get_typings()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional, Type

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.task.task_input_model import TaskInputModel

from ...core.classes.jsonable import Jsonable, ListJsonable
from ...core.classes.paginator import Paginator
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.exception.exceptions.not_found_exception import NotFoundException
from ...core.service.base_service import BaseService
from ...model.typing_manager import TypingManager
from ...resource.resource import Resource
from ...resource.resource_model import ResourceModel, ResourceOrigin
from ...resource.resource_typing import FileTyping
from .file import File
from .file_store import FileStore
from .local_file_store import LocalFileStore


class FileService(BaseService):

    @classmethod
    def fetch_file_list(cls,
                        page: Optional[int] = 1,
                        number_of_items_per_page: Optional[int] = 20) -> Paginator:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = ResourceModel.select().where(
            (ResourceModel.origin == ResourceOrigin.IMPORTED) & (ResourceModel.fs_node_model is not None)).order_by(
            ResourceModel.creation_datetime.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    # -- D --

    @classmethod
    def download_file(cls, uri: str) -> FileResponse:
        resource_model: ResourceModel = ResourceModel.get_by_uri_and_check(uri)
        resource: Resource = resource_model.get_resource()

        if not isinstance(resource, File):
            raise BadRequestException(f"The resource is not a file")

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.node_name_exists(resource.name):
            raise NotFoundException(f"The file '{resource.name}' does not exists on the server. It has been deleted")

        return FileResponse(resource.path, media_type='application/octet-stream', filename=resource.name)

    # -- U --

    @classmethod
    async def upload_files(cls, files: List[UploadFile] = FastAPIFile(...), typing_names: List[str] = None) -> Jsonable:

        file_store: FileStore = LocalFileStore.get_default_instance()

        result: ListJsonable = ListJsonable()
        for index, file in enumerate(files):
            file_model: ResourceModel = cls.upload_file_to_store(file, typing_names[index], file_store)
            result.append(file_model)

        return result

    @classmethod
    def upload_file_to_store(cls, upload_file: UploadFile, typing_name: str, store: FileStore) -> ResourceModel:

        file_type: Type[File] = TypingManager.get_type_from_name(typing_name)

        file: File = store.add_from_temp_file(upload_file.file, upload_file.filename, file_type)

        file_model: ResourceModel = ResourceModel.from_resource(file)
        file_model.origin = ResourceOrigin.IMPORTED
        return file_model.save_full()

    @classmethod
    def create_file_model(cls, file: File) -> ResourceModel:
        file_model: ResourceModel = ResourceModel.from_resource(file)
        file_model.origin = ResourceOrigin.IMPORTED
        return file_model.save_full()

    @classmethod
    def add_file_to_default_store(cls, file: File, dest_file_name: str = None) -> ResourceModel:
        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        return cls._add_file_to_store(file=file, store=file_store, dest_file_name=dest_file_name)

    @classmethod
    def add_file_to_store(cls, file: File, store_uri: str, dest_file_name: str = None) -> ResourceModel:
        file_store: LocalFileStore = FileStore.get_by_uri_and_check(store_uri)
        return cls._add_file_to_store(file=file, store=file_store, dest_file_name=dest_file_name)

    @classmethod
    def _add_file_to_store(cls, file: File, store: FileStore, dest_file_name: str = None) -> ResourceModel:
        new_file: File = store.add_file_from_path(source_path=file, dest_file_name=dest_file_name)
        return cls.create_file_model(new_file)

    @classmethod
    def delete_file(cls, file_uri: str) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_uri_and_check(file_uri)

        if resource_model.origin != ResourceOrigin.IMPORTED:
            raise BadRequestException(GWSException.DELETE_GENERATED_FILE_ERROR.value,
                                      GWSException.DELETE_USED_FILE_ERROR.value)

        task_input: TaskInputModel = TaskInputModel.get_by_resource_model(resource_model.id).first()

        if task_input:
            raise BadRequestException(GWSException.DELETE_USED_FILE_ERROR.value,
                                      unique_code=GWSException.DELETE_USED_FILE_ERROR.value,
                                      detail_args={"experiment_uri": task_input.experiment.get_short_name()})

        resource_model.delete_instance()


############################# FILE TYPE ###########################


    @classmethod
    def get_file_types(cls) -> List[FileTyping]:
        return FileTyping.get_typings()

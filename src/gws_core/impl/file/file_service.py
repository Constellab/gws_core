# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException

from ...core.classes.jsonable import Jsonable, ListJsonable
from ...core.classes.paginator import Paginator
from ...core.service.base_service import BaseService
from .file import File
from .file_resource import FileResource
from .file_store import FileStore
from .local_file_store import LocalFileStore


class FileService(BaseService):

    @classmethod
    def fetch_file_list(cls,
                        page: Optional[int] = 1,
                        number_of_items_per_page: Optional[int] = 20) -> Paginator:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = FileResource.select().order_by(FileResource.creation_datetime.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    # -- D --

    @classmethod
    def download_file(cls, uri: str) -> FileResponse:
        file_resource: FileResource = FileResource.get_by_uri_and_check(uri)
        file: File = file_resource.get_resource()

        file_store: FileStore = LocalFileStore.get_default_instance()
        if not file_store.file_exists(file.name):
            raise NotFoundException(f"The file '{file.name}' does not exists on the server. It has been deleted")

        return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)

    # -- U --

    @classmethod
    async def upload_files(cls, files: List[UploadFile] = FastAPIFile(...)) -> Jsonable:

        file_store: FileStore = LocalFileStore.get_default_instance()

        if len(files) == 1:
            file = files[0]
            return cls.upload_file_to_store(file, file_store)
        else:
            result: ListJsonable = ListJsonable()
            for file in files:
                file_resource: FileResource = cls.upload_file_to_store(file, file_store)
                result.append(file_resource)

            return result

    @classmethod
    def upload_file_to_store(cls, upload_file: UploadFile, store: FileStore) -> FileResource:
        file: File = store.add_from_temp_file(upload_file.file, upload_file.filename)
        return cls.create_file_resource(file)

    @classmethod
    def create_file_resource(cls, file: File) -> FileResource:
        file_resource: FileResource = FileResource.from_resource(file)
        return file_resource.save()

    @classmethod
    def add_file_to_default_store(cls, file: File, dest_file_name: str = None) -> FileResource:
        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        return cls._add_file_to_store(file=file, store=file_store)

    @classmethod
    def add_file_to_store(cls, file: File, store_uri: str, dest_file_name: str = None) -> FileResource:
        file_store: LocalFileStore = FileStore.get_by_uri_and_check(store_uri)
        return cls._add_file_to_store(file=file, store=file_store)

    @classmethod
    def _add_file_to_store(cls, file: File, store: FileStore, dest_file_name: str = None) -> FileResource:
        file: File = store.add_from_file(source_file=file, dest_file_name=dest_file_name)
        return cls.create_file_resource(file)

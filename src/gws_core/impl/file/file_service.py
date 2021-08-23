# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional, Union

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.impl.file.file import File

from ...core.classes.paginator import Paginator
from ...core.exception.exceptions import NotFoundException
from ...core.service.base_service import BaseService
from .file_resource import FileResource
from .file_store import FileStore, LocalFileStore


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
        try:
            file: FileResource = FileResource.get_by_uri_and_check(uri)
            return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
        except Exception as err:
            raise NotFoundException(
                detail=f"File not found with uri '{uri}'") from err

    # -- U --

    @classmethod
    async def upload_file(cls, files: List[UploadFile] = FastAPIFile(...)) -> Union[FileResource, List[FileResource]]:

        file_store: FileStore = LocalFileStore.get_default_instance()

        if len(files) == 1:
            file = files[0]
            return file_store.add(file.file, dest_file_name=file.filename)
        else:
            result: List[FileResource] = []
            # t = self.out_port("file_set").get_default_resource_type()
            # file_set = t()
            for file in files:
                f = file_store.add(file.file, dest_file_name=file.filename)
                result.append(f)

            return result

    @classmethod
    def create_file_resource(cls, file: File) -> FileResource:
        file_resource: FileResource = FileResource.from_resource(file)
        return file_resource.save()

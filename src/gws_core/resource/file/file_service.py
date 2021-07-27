# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional, Union

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse

from ...core.classes.paginator import Paginator
from ...core.exception import BadRequestException, NotFoundException
from ...core.model.study import Study
from ...core.service.base_service import BaseService
from ...model.model_service import ModelService
from ...user.current_user_service import CurrentUserService
from .file import File, FileSet
from .file_uploader import FileUploader


class FileService(BaseService):

    @classmethod
    def fetch_file_list(cls,
                        type="gws.file.File",
                        search_text: Optional[str] = "",
                        page: Optional[int] = 1,
                        number_of_items_per_page: Optional[int] = 20,
                        as_json: bool = False) -> Union[Paginator, List[File], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise NotFoundException(detail=f"File type '{type}' not found")
        else:
            t = File
        if search_text:
            query = t.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = t.select().order_by(t.creation_datetime.desc())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    # -- D --

    @classmethod
    def download_file(cls, type, uri) -> FileResponse:
        t = ModelService.get_model_type(type)
        if t is None:
            raise NotFoundException(detail=f"File type '{type}' not found")
        try:
            file = t.get(t.uri == uri)
            return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
        except Exception as err:
            raise NotFoundException(
                detail=f"File not found with uri '{uri}'") from err

    # -- U --

    @classmethod
    async def upload_file(cls, files: List[UploadFile] = FastAPIFile(...), study_uri=None) -> Union[FileSet, File]:
        uploader = FileUploader(files=files)
        user = CurrentUserService.get_current_user()
        if study_uri is None:
            e = uploader.create_experiment(study=Study.get_default_instance())
            e.set_title("File upload")
            e.save()
        else:
            try:
                study = Study.get(Study.uri == study_uri)
                e = uploader.create_experiment(study=study, user=user)
                e.set_title("File upload")
                e.save()
            except Exception as err:
                raise NotFoundException(detail=f"Study not found") from err
        try:
            await e.run(wait_response=True)
            return uploader.output["result"]
        except Exception as err:
            raise BadRequestException(detail=f"Upload failed. Error: {err}")

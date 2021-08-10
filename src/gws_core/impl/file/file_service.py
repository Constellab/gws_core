# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import traceback
from typing import List, Optional, Type, Union

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.responses import FileResponse
from gws_core.model.typing_manager import TypingManager

from ...core.classes.paginator import Paginator
from ...core.exception.exceptions import BadRequestException, NotFoundException
from ...core.model.model import Model
from ...core.service.base_service import BaseService
from ...experiment.experiment_service import ExperimentService
from ...study.study import Study
from ...user.current_user_service import CurrentUserService
from .file import File, FileSet
from .file_uploader import FileUploader


class FileService(BaseService):

    @classmethod
    def fetch_file_list(cls,
                        typing_name="RESOURCE.gws_core.file",
                        search_text: Optional[str] = "",
                        page: Optional[int] = 1,
                        number_of_items_per_page: Optional[int] = 20,
                        as_json: bool = False) -> Union[Paginator, List[File], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type = None
        if typing_name:
            model_type = TypingManager.get_type_from_name(typing_name)
            if model_type is None:
                raise NotFoundException(
                    detail=f"File type '{typing_name}' not found")
        else:
            model_type = File
        if search_text:
            query = model_type.search(search_text)
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
                'paginator': paginator.paginator_dict()
            }
        else:
            query = model_type.select().order_by(model_type.creation_datetime.desc())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    # -- D --

    @classmethod
    def download_file(cls, typing_name, uri) -> FileResponse:
        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)
        if model_type is None:
            raise NotFoundException(
                detail=f"File type '{typing_name}' not found")
        try:
            file = model_type.get(model_type.uri == uri)
            return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
        except Exception as err:
            raise NotFoundException(
                detail=f"File not found with uri '{uri}'") from err

    # -- U --

    @classmethod
    async def upload_file(cls, files: List[UploadFile] = FastAPIFile(...)) -> Union[FileSet, File]:
        uploader = FileUploader(files=files)
        experiment = ExperimentService.create_experiment_from_process(
            process=uploader, title="File upload")

        try:
            await ExperimentService.run_experiment(experiment_uri=experiment.uri)
            return uploader.output["result"]
        except Exception as err:
            traceback.print_exc()
            raise BadRequestException(detail=f"Upload failed. Error: {err}")

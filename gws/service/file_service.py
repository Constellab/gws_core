# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from fastapi import UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse

from gws.query import Paginator
from gws.file import File, FileUploader
from gws.model import Study
from gws.http import *

from .base_service import BaseService
from .model_service import ModelService
from .user_service import UserService

class FileService(BaseService):
    
    @classmethod
    def fetch_file_list(cls, page=1, number_of_items_per_page=20) -> list:
        pass
    
    # -- D --
    @classmethod
    def download_file(cls, type, uri):
        t = ModelService.get_model_type(type)
        if t is None:
            raise HTTPNotFound(detail=f"File type '{type}' not found")
            
        try:
            file = t.get(t.uri == uri)
            return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
        except:
            raise HTTPNotFound(detail=f"File not found with uri '{uri}'")

    # -- U --
    
    @classmethod
    async def upload_file(cls, files: List[UploadFile] = FastAPIFile(...), study_uri=None):
        uploader = FileUploader(files=files)
        user = UserService.get_current_user()
        
        if study_uri is None:
            e = uploader.create_experiment(study=Study.get_default_instance())
        else:
            try:
                study = Study.get(Study.uri == study_uri)
                e = uploader.create_experiment(study=study, user=user)
            except:
                raise HTTPNotFound(detail=f"Study not found")

        try:
            await e.run(wait_response=True)
            result = uploader.output["result"]
            return result.to_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"Upload failed. Error: {err}")
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional, List
from fastapi import Depends, FastAPI, \
                    UploadFile, File as FastAPIFile

from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.put("/file/upload", tags=["Upload and download files"])
async def upload_file(files: List[UploadFile] = FastAPIFile(...), \
                 study_uri:Optional[str] = None, \
                 _: UserData = Depends(check_user_access_token)):
    """
    Upload files
    
    - **study_uri**: the uri of the current study. If not given, the default **study** is used.
    """
    
    from gws.service.file_service import FileService
    
    return await FileService.upload_file(files=files, study_uri=study_uri)

@core_app.get("/file/{type}/{uri}/download", tags=["Upload and download files"])
async def download_file(type: str, \
                        uri: str, \
                        _: UserData = Depends(check_user_access_token)):
    """
    Download a file
    
    - **type**: the type of the file to download
    - **uri**: the uri of the file to download
    """
    
    from gws.service.file_service import FileService
    
    return FileService.download_file(type=type, uri=uri)
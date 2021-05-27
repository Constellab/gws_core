# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws.dto.user_dto import UserData
from typing import Optional, List
from fastapi import Depends, \
                    UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse

from gws.service.file_service import FileService
from ._auth_user import check_user_access_token
from .core_app import core_app

@core_app.post("/file/upload", tags=["Files"], summary="Upload a file or a list of files")
async def upload_a_file_or_list_of_files(files: List[UploadFile] = FastAPIFile(...), \
                      study_uri:Optional[str] = None, \
                      _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Upload files
    
    - **study_uri**: the uri of the current study. If not given, the default **study** is used.
    """
    
    file = await FileService.upload_file(files=files, study_uri=study_uri)
    return file.to_json()

@core_app.get("/file/{type}/{uri}/download", tags=["Files"], summary="Download a file")
async def download_a_file(type: str, \
                        uri: str, \
                        _: UserData = Depends(check_user_access_token)) -> FileResponse:
    """
    Download a file
    
    - **type**: the type of the file to download
    - **uri**: the uri of the file to download
    """

    file_response = FileService.download_file(type=type, uri=uri)
    return file_response

@core_app.get("/file/{type}", tags=["Files"], summary="Get the list of files")
async def get_the_list_of_files(type: Optional[str] = "gws.file.File", \
                                  search_text: Optional[str] = "", \
                                  page: Optional[int] = 1, \
                                  number_of_items_per_page: Optional[int] = 20, \
                                  _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a list of experiments. The list is paginated.

    - **type**: the type of the file to search
    - **number_of_items_per_page**: the number of items per page (limited to 50) s
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """
    
    return FileService.fetch_file_list(
        type=type,
        search_text=search_text,
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json  = True,
    )
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.user.auth_service import AuthService
from gws_core.user.user_credentials_dto import UserCredentialsDTO

from ..core_app import core_app
from .credentials_dto import CredentialDTO, SaveCredentialDTO
from .credentials_service import CredentialsService


@core_app.post("/credentials")
async def create_credentials(credentials: SaveCredentialDTO,
                             _=Depends(AuthService.check_user_access_token)) -> CredentialDTO:
    return CredentialsService.create(credentials).to_dto()


@core_app.put("/credentials/{id}")
async def update_credentials(id: str,
                             credentials: SaveCredentialDTO,
                             _=Depends(AuthService.check_user_access_token)) -> CredentialDTO:
    return CredentialsService.update(id, credentials).to_dto()


@core_app.delete("/credentials/{id}")
async def delete_credentials(id: str,
                             _=Depends(AuthService.check_user_access_token)) -> None:
    CredentialsService.delete(id)


@core_app.get("/credentials/{id}")
async def get_credentials(id: str,
                          _=Depends(AuthService.check_user_access_token)) -> CredentialDTO:
    return CredentialsService.get_by_id_and_check(id).to_dto()


@core_app.get("/credentials")
async def get_all(page: int = 0,
                  number_of_items_per_page: int = 20,
                  _=Depends(AuthService.check_user_access_token)) -> PageDTO[CredentialDTO]:
    return CredentialsService.get_all(page, number_of_items_per_page).to_dto()


@core_app.post("/credentials/{id}/data")
async def read_credentials(id: str,
                           user_credentials: UserCredentialsDTO,
                           _=Depends(AuthService.check_user_access_token)) -> dict:
    return CredentialsService.get_credentials_data(id, user_credentials)


@core_app.get("/credentials/name/{name}")
async def get_credentials_by_name(name: str,
                                  _=Depends(AuthService.check_user_access_token)) -> Optional[CredentialDTO]:
    credentials = CredentialsService.find_by_name(name)
    if credentials:
        return credentials.to_dto()
    else:
        return None


@core_app.post("/credentials/search")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[CredentialDTO]:
    return CredentialsService.search(search_dict, page, number_of_items_per_page).to_dto()



from typing import Optional

from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.user.authorization_service import AuthorizationService
from gws_core.user.user_credentials_dto import UserCredentialsDTO

from ..core_controller import core_app
from .credentials_service import CredentialsService
from .credentials_type import (CredentialsDataSpecsDTO, CredentialsDTO,
                               SaveCredentialsDTO)


@core_app.post("/credentials")
def create_credentials(credentials: SaveCredentialsDTO,
                       _=Depends(AuthorizationService.check_user_access_token)) -> CredentialsDTO:
    return CredentialsService.create(credentials).to_dto()


@core_app.put("/credentials/{id_}")
def update_credentials(id_: str,
                       credentials: SaveCredentialsDTO,
                       _=Depends(AuthorizationService.check_user_access_token)) -> CredentialsDTO:
    return CredentialsService.update(id_, credentials).to_dto()


@core_app.delete("/credentials/{id_}")
def delete_credentials(id_: str,
                       _=Depends(AuthorizationService.check_user_access_token)) -> None:
    CredentialsService.delete(id_)


@core_app.get("/credentials/{id_}")
def get_credentials(id_: str,
                    _=Depends(AuthorizationService.check_user_access_token)) -> CredentialsDTO:
    return CredentialsService.get_by_id_and_check(id_).to_dto()


@core_app.get("/credentials")
def get_all(page: int = 0,
            number_of_items_per_page: int = 20,
            _=Depends(AuthorizationService.check_user_access_token)) -> PageDTO[CredentialsDTO]:
    return CredentialsService.get_all(page, number_of_items_per_page).to_dto()


@core_app.post("/credentials/{id_}/data")
def read_credentials(id_: str,
                     user_credentials: UserCredentialsDTO,
                     _=Depends(AuthorizationService.check_user_access_token)) -> dict:
    return CredentialsService.get_credentials_data(id_, user_credentials)


@core_app.get("/credentials/name/{name}")
def get_credentials_by_name(name: str,
                            _=Depends(AuthorizationService.check_user_access_token)) -> Optional[CredentialsDTO]:
    credentials = CredentialsService.find_by_name(name)
    if credentials:
        return credentials.to_dto()
    else:
        return None


@core_app.post("/credentials/search")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthorizationService.check_user_access_token)) -> PageDTO[CredentialsDTO]:
    return CredentialsService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/credentials/data/specs")
def get_credentials_data_specs(_=Depends(AuthorizationService.check_user_access_token)) -> CredentialsDataSpecsDTO:
    return CredentialsService.get_credentials_data_specs()

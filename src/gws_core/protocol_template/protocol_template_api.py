# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core_app import core_app
from gws_core.user.auth_service import AuthService

from .protocol_template_service import ProtocolTemplateService


@core_app.get("/protocol-template/{id}", tags=["Protocol template"], summary="Get an protocol template")
def get_by_id(id: str,
              _=Depends(AuthService.check_user_access_token)) -> dict:

    return ProtocolTemplateService.get_by_id_and_check(id=id).to_json(deep=True)


@core_app.delete("/protocol-template/{id}", tags=["Protocol template"], summary="Delete an protocol template")
def delete_by_id(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:

    ProtocolTemplateService.delete(id=id)


@core_app.post("/protocol-template/search", tags=["Protocol template"], summary="Advanced search for protocol template")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search on protocol template
    """
    return ProtocolTemplateService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.get("/protocol-template/search-name/{name}", tags=["Protocol template"],
              summary="Search for protocol template by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> dict:
    return ProtocolTemplateService.search_by_name(name, page, number_of_items_per_page).to_json()

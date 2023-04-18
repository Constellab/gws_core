# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from fastapi.param_functions import Depends
from pydantic.main import BaseModel

from ..core.classes.jsonable import ListJsonable
from ..core_app import core_app
from ..user.auth_service import AuthService
from .tag_service import TagService


# DTO to create/update an experiment
class NewTagDTO(BaseModel):
    key: str
    value: str


@core_app.get("/tag/{key}", tags=["Tag"], summary='Search tag by key')
def search_by_key(key: str,
                  _=Depends(AuthService.check_user_access_token)):
    """
    Search tags by key.
    """

    tags = TagService.search_by_key(key)
    return ListJsonable(tags).to_json()


@core_app.get("/tag", tags=["Tag"], summary='Get all tags')
def get_all(_=Depends(AuthService.check_user_access_token)):

    tags = TagService.get_all_tags()
    return ListJsonable(tags).to_json()


@core_app.post("/tag/{key}/{value}", tags=["Tag"], summary='Register a new tag')
def register_tag(key: str,
                 value: str,
                 _=Depends(AuthService.check_user_access_token)):
    return TagService.register_tag(key, value).to_json()


@core_app.put("/tag/{tag_key}/reorder", tags=["Tag"], summary='Reoarder tags')
def reorder_tag_values(tag_key: str,
                       tags_values: List[str],
                       _=Depends(AuthService.check_user_access_token)):
    return TagService.reorder_tag_values(tag_key, tags_values).to_json()


@core_app.put("/tag/reorder", tags=["Tag"], summary='Reoarder tags')
def reorder_tags(tags_keys: List[str],
                 _=Depends(AuthService.check_user_access_token)):
    return ListJsonable(TagService.reorder_tags(tags_keys)).to_json()


@core_app.put("/tag/{key}/{old_value}/{new_value}", tags=["Tag"], summary='Update registered tag value')
def update_registered_tag_value(key: str,
                                old_value: str,
                                new_value: str,
                                _=Depends(AuthService.check_user_access_token)):
    return TagService.update_registered_tag_value(key, old_value, new_value).to_json()


@core_app.delete("/tag/{key}/{value}", tags=["Tag"], summary='Delete registered tag')
def delete_registered_tag(key: str,
                          value: str,
                          _=Depends(AuthService.check_user_access_token)):
    return TagService.delete_registered_tag(key, value)

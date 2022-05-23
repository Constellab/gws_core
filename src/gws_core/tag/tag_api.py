# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi.param_functions import Depends
from pydantic.main import BaseModel

from ..core.classes.jsonable import ListJsonable
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .tag_service import TagService


# DTO to create/update an experiment
class NewTagDTO(BaseModel):
    key: str
    value: str


@core_app.get("/tag/{key}", tags=["Tag"], summary='Search tag by key')
async def search_by_key(key: str,
                        _: UserData = Depends(AuthService.check_user_access_token)):
    """
    Search tags by key.
    """

    tags = TagService.search_by_key(key)
    return ListJsonable(tags).to_json()


@core_app.get("/tag", tags=["Tag"], summary='Get all tags')
async def get_all(_: UserData = Depends(AuthService.check_user_access_token)):

    tags = TagService.get_all_tags()
    return ListJsonable(tags).to_json()


@core_app.post("/tag/{key}/{value}", tags=["Tag"], summary='Register a new tag')
async def register_tag(key: str,
                       value: str,
                       _: UserData = Depends(AuthService.check_user_access_token)):
    return TagService.register_tag(key, value).to_json()


@core_app.put("/tag/{key}/{old_value}/{new_value}", tags=["Tag"], summary='Update registered tag value')
async def update_registered_tag_value(key: str,
                                      old_value: str,
                                      new_value: str,
                                      _: UserData = Depends(AuthService.check_user_access_token)):
    return TagService.update_registered_tag_value(key, old_value, new_value).to_json()


@core_app.delete("/tag/{key}/{value}", tags=["Tag"], summary='Delete registered tag')
async def delete_registered_tag(key: str,
                                value: str,
                                _: UserData = Depends(AuthService.check_user_access_token)):
    return TagService.delete_registered_tag(key, value)

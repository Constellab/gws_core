# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi.param_functions import Depends
from pydantic.main import BaseModel

from ..core.classes.jsonable import ListJsonable
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .tag import Tag
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


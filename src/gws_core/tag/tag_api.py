
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


@core_app.get("/tag", tags=["Tag"], summary='Get all tags')
async def get_tag(key: str,
                  page: Optional[int] = 1,
                  number_of_items_per_page: Optional[int] = 20,
                  _: UserData = Depends(AuthService.check_user_access_token)):
    """
    Get all tags.
    """

    return TagService.search_by_key(key, page, number_of_items_per_page).to_json()


@core_app.post("/tag/add/{typing_name}/{id}", tags=["Tag"], summary='Add a tag to a model')
def add_tag(typing_name: str, id: str, tag: NewTagDTO,
            _: UserData = Depends(AuthService.check_user_access_token)) -> List[Tag]:

    return TagService.add_tag_to_model(typing_name, id, tag.key, tag.value)


@core_app.put("/tag/save/{typing_name}/{id}", tags=["Tag"], summary='Save all tag for a model')
def save_tag(typing_name: str, id: str, tags: List[Tag],
             _: UserData = Depends(AuthService.check_user_access_token)) -> List[Tag]:

    return TagService.save_tags_to_model(typing_name, id, tags)

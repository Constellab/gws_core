# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user_group import UserGroup


class UserTheme(Enum):
    LIGHT_THEME = 'light-theme'
    DARK_THEME = 'dark-theme'


class UserLanguage(Enum):
    EN = 'en'
    FR = 'fr'

# object that represent the user in the Space


class UserSpace(BaseModel):
    id: str
    firstname: str
    lastname: str
    email: str
    theme: UserTheme
    lang: UserLanguage
    photo: Optional[str]


class Space(BaseModel):
    id: str
    name: str
    domain: str
    photo: Optional[str]


# Info provided by the user when he logs in
class UserLoginInfo(BaseModel):
    user: UserSpace
    space: Space


class SpaceDict(TypedDict):
    id: str
    name: str
    domain: str
    photo: Optional[str]


class UserDTO(BaseModelDTO):
    id: str
    email: str
    first_name: str
    last_name: str
    photo: Optional[str]


class UserFullDTO(UserDTO):
    id: str
    email: str
    first_name: str
    last_name: str
    group: UserGroup
    is_active: bool
    theme: Optional[UserTheme]
    lang: Optional[UserLanguage]
    photo: Optional[str]

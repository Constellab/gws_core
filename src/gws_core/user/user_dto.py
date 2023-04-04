# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Optional

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict


class UserTheme(Enum):
    LIGHT_THEME = 'light-theme'
    DARK_THEME = 'dark-theme'


class UserLanguage(Enum):
    EN = 'en'
    FR = 'fr'


class UserDataDict(TypedDict):
    id: str
    email: str
    first_name: str
    last_name: str
    group: str
    is_active: bool
    theme: NotRequired[str]
    lang: NotRequired[str]


# object that represent the user in the Space
class UserSpace(BaseModel):
    id: str
    firstname: str
    lastname: str
    email: str
    theme: UserTheme
    lang: UserLanguage


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

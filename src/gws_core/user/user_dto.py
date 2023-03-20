# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from gws_core.user.user import UserLanguage, UserTheme
from pydantic import BaseModel

from ..user.user_group import UserGroup


class UserData(BaseModel):
    id: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    group: UserGroup
    is_active: bool

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

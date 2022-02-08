from typing import TypedDict

from gws_core.user.user import UserTheme
from pydantic import BaseModel

from ..user.user_group import UserGroup


class UserData(BaseModel):
    id: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    group: UserGroup
    is_active: bool
    is_admin: bool


class UserCentral(BaseModel):
    id: str
    firstname: str
    lastname: str
    email: str
    theme: UserTheme

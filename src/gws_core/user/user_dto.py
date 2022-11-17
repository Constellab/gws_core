# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pydantic import BaseModel

from gws_core.user.user import UserLanguage, UserTheme

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
    lang: UserLanguage


class OrganizationCentral(BaseModel):
    id: str
    label: str
    domain: str
    photo: str

# Info provided by the user when he logs in


class UserLoginInfo(BaseModel):
    user: UserCentral
    organization: OrganizationCentral

from enum import Enum
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user_group import UserGroup
from typing_extensions import TypedDict


class UserTheme(Enum):
    LIGHT_THEME = "light-theme"
    DARK_THEME = "dark-theme"


class UserLanguage(Enum):
    EN = "en"
    FR = "fr"


# object that represent the user in the Space


class UserSpace(BaseModelDTO):
    id: str
    firstname: str
    lastname: str
    email: str
    theme: UserTheme
    lang: UserLanguage
    photo: Optional[str]


class Space(BaseModelDTO):
    id: str
    name: str
    domain: str
    photo: Optional[str]


# Info provided by the user when he logs in
class UserLoginInfo(BaseModelDTO):
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

    @staticmethod
    def from_user_space(user_space: UserSpace | dict) -> "UserDTO":
        if not user_space:
            return None
        if isinstance(user_space, dict):
            user_space = UserSpace.from_json(user_space)
        return UserDTO(
            id=user_space.id,
            email=user_space.email,
            first_name=user_space.firstname,
            last_name=user_space.lastname,
            photo=user_space.photo,
        )


class UserFullDTO(UserDTO):
    id: str
    email: str
    first_name: str
    last_name: str
    group: UserGroup
    is_active: bool
    theme: UserTheme = UserTheme.LIGHT_THEME
    lang: UserLanguage = UserLanguage.EN
    photo: Optional[str] = None

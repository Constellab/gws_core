
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from gws_core.share.share_link import ShareLink

from gws_core.user.user import User


class AuthContextBase:

    context_type: Literal['user', 'app', 'share-link']

    def __init__(self, context_type: Literal['user', 'app', 'share-link']) -> None:
        self.context_type = context_type

    @abstractmethod
    def get_user(self) -> User:
        pass


class AuthContextUser(AuthContextBase):

    context_type: Literal['user'] = 'user'
    user: User

    def __init__(self, user: User) -> None:
        super().__init__('user')
        self.user = user

    def get_user(self) -> User:
        return self.user


class AuthContextApp(AuthContextBase):

    context_type: Literal['app'] = 'app'
    app_id: str
    user: User

    def __init__(self,
                 app_id: str, user: User) -> None:
        super().__init__('app')
        self.app_id = app_id
        self.user = user

    def get_app_id(self) -> str:
        return self.app_id

    def get_user(self) -> User:
        return self.user


class AuthContextShareLink(AuthContextBase):

    context_type: Literal['share-link'] = 'share-link'
    share_link: ShareLink
    user: User

    def __init__(self,
                 share_link: ShareLink, user: User) -> None:
        super().__init__('share-link')
        self.share_link = share_link
        self.user = user

    def get_share_link(self) -> ShareLink:
        return self.share_link

    def get_user(self) -> User:
        return self.user


AuthContext = AuthContextUser | AuthContextApp | AuthContextShareLink



from typing import Optional, final

from peewee import BooleanField, CharField, ModelSelect

from ..core.classes.enum_field import EnumField
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from .user_dto import UserDTO, UserFullDTO, UserLanguage, UserTheme
from .user_group import UserGroup


@final
class User(Model):
    """
    User class

    :property email: The user email
    :type email: `str`
    :property group: The user group (`sysuser`, `admin`, `owner` or `user`)
    :type group: `str`
    :property is_active: True if the is active, False otherwise
    :type is_active: `bool`
    """

    email: str = CharField(default=False, index=True)
    first_name: str = CharField(default=False)
    last_name: str = CharField(default=False)
    group: UserGroup = EnumField(choices=UserGroup,
                                 default=UserGroup.USER)
    is_active = BooleanField(default=True)
    theme: UserTheme = EnumField(choices=UserTheme,
                                 default=UserTheme.LIGHT_THEME)

    lang: UserLanguage = EnumField(choices=UserLanguage,
                                   default=UserLanguage.EN)

    photo: str = CharField(null=True)

    _table_name = 'gws_user'

    @classmethod
    def get_sysuser(cls) -> 'User':
        return User.get(User.group == UserGroup.SYSUSER)

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return User.get(User.email == email)

    @classmethod
    def search_by_firstname_or_lastname(cls, search: str) -> ModelSelect:
        return User.select().where(
            (User.group != UserGroup.SYSUSER) &
            ((User.first_name.contains(search)) | (User.last_name.contains(search)))
        ).order_by(User.first_name, User.last_name)

    @classmethod
    def search_by_firstname_and_lastname(cls, name1: str, name2: str) -> ModelSelect:
        return User.select().where(
            (User.group != UserGroup.SYSUSER) &
            (((User.first_name.contains(name1)) & (User.last_name.contains(name2))) |
             ((User.first_name.contains(name2)) & (User.last_name.contains(name1))))
        ).order_by(User.first_name, User.last_name)

    @property
    def full_name(self):
        return " ".join([self.first_name, self.last_name]).strip()

    @property
    def is_owner(self):
        return self.group == UserGroup.OWNER

    @property
    def is_sysuser(self):
        return self.group == UserGroup.SYSUSER

    def has_access(self, group: UserGroup) -> bool:
        """return true if the user group is equal or higher than the group
        """
        return self.group <= group

    def has_dark_theme(self) -> bool:
        return self.theme == UserTheme.DARK_THEME

    def save(self, *arg, **kwargs) -> 'User':
        if not UserGroup.has_value(self.group):
            raise BadRequestException("Invalid user group")
        return super().save(*arg, **kwargs)

    def to_dto(self) -> UserDTO:
        return UserDTO(
            id=self.id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            photo=self.photo
        )

    def to_full_dto(self) -> UserFullDTO:
        return UserFullDTO(
            id=self.id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            group=self.group,
            is_active=self.is_active,
            theme=self.theme,
            lang=self.lang,
            photo=self.photo
        )

    def from_full_dto(self, data: UserFullDTO) -> None:
        self.email = data.email
        self.first_name = data.first_name
        self.last_name = data.last_name
        self.group = data.group or UserGroup.USER
        self.is_active = data.is_active
        self.theme = data.theme or UserTheme.LIGHT_THEME
        self.lang = data.lang or UserLanguage.EN
        self.photo = data.photo

from enum import Enum

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException


# Enum to define the role needed for a protocol
class UserGroup(Enum):
    SYSUSER = "SYSUSER"
    OWNER = "OWNER"
    USER = "USER"

    @classmethod
    def has_value(cls, user_group: 'UserGroup') -> bool:
        return user_group.value in cls._value2member_map_

    @classmethod
    def get_value(cls, user_group: 'UserGroup') -> int:
        if not cls.has_value(user_group):
            raise BadRequestException(f"The user group {user_group} doesn't exists")

        switcher = {
            UserGroup.SYSUSER: 0,
            UserGroup.OWNER: 5,
            UserGroup.USER: 15,
        }
        return switcher.get(user_group)

    def __lt__(self, other: 'UserGroup') -> bool:
        return UserGroup.get_value(self) < UserGroup.get_value(other)

    def __le__(self, other: 'UserGroup') -> bool:
        return UserGroup.get_value(self) <= UserGroup.get_value(other)

    def __gt__(self, other: 'UserGroup') -> bool:
        return UserGroup.get_value(self) > UserGroup.get_value(other)

    def __ge__(self, other) -> bool:
        return UserGroup.get_value(self) >= UserGroup.get_value(other)

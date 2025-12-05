from enum import Enum
from typing import Any

from peewee import CharField, IntegerField

from gws_core.core.utils.string_helper import StringHelper


class EnumField(CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, *args: Any, choices: type, max_length: int = 255, **kwargs: Any) -> None:
        super().__init__(max_length=max_length, *args, **kwargs)
        self.choices = choices

    def db_value(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        return value

    def python_value(self, value: Any) -> Any:
        return StringHelper.to_enum(self.choices, value)


class IntEnumField(IntegerField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, *args: Any, choices: type, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices

    def db_value(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        return value

    def python_value(self, value: Any) -> Any:
        return StringHelper.to_enum(self.choices, value)

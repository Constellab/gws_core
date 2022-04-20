from enum import Enum
from typing import Any, Type

from gws_core.core.utils.utils import Utils
from peewee import CharField


class EnumField(CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, choices: Type, *args: Any, **kwargs: Any) -> None:
        super(CharField, self).__init__(*args, **kwargs)
        self.choices = choices
        self.max_length = 255

    def db_value(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        return value

    def python_value(self, value: Any) -> Any:
        return Utils.str_to_enum(self.choices, value)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from peewee import CharField, Expression
from pydantic.main import BaseModel

from ..core.classes.expression_builder import ExpressionBuilder

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

# List of default tag with values
default_tags = {
    "status": ['SUCCESS', 'WARNING', 'ERROR'],
    "type": ['DATA', 'ARRAY', 'EXPERIMENT', 'JSON'],
    "name": []
}
MAX_TAG_LENGTH = 30


class Tag(BaseModel):
    key: str = None
    value: str = None

    def __init__(self, key: str, value: str) -> None:
        super().__init__(key=self._check_parse_key(key), value=self._check_parse_value(value))

    def set_key(self, key: str) -> None:
        self.key = self._check_parse_key(key)

    def set_value(self, value: str) -> None:
        self.value = self._check_parse_value(value)

    def _check_parse_key(self, key: str) -> str:
        if key is None:
            raise ValueError('The tag key must be defined')
        if len(key) > MAX_TAG_LENGTH:
            key = key[0: MAX_TAG_LENGTH]

        return key.lower()

    def _check_parse_value(self, value: str) -> str:
        if value:
            value = value.lower()
            if len(value) > MAX_TAG_LENGTH:
                value = value[0: MAX_TAG_LENGTH]

        return value

    def __str__(self) -> str:
        return self.key + ':' + self.value

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Tag):
            return False
        return (self is o) or (self.key == o.key and self.value == o.value)

    @staticmethod
    def from_string(tag_str: str) -> 'Tag':
        if not tag_str:
            return None

        tag_info: List[str] = tag_str.split(KEY_VALUE_SEPARATOR)

        # Tag without a value
        if len(tag_info) == 1:
            return Tag(tag_info[0], '')
        else:
            return Tag(tag_info[0], tag_info[1])

    def to_json(self) -> Dict:
        return {"key": self.key, "value": self.value}

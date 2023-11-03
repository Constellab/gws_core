# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from re import match
from typing import Dict, List

from pydantic.main import BaseModel

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

MAX_TAG_LENGTH = 1000


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

        return Tag.check_parse_tag_str(key)

    def _check_parse_value(self, value: str) -> str:
        if value:
            value = Tag.check_parse_tag_str(value)
        return value

    def __str__(self) -> str:
        return self.key + KEY_VALUE_SEPARATOR + self.value

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

    @staticmethod
    def check_parse_tag_str(tag_str: str) -> str:
        """Method that check the length of the tag str (key or value) and that the tag str is valid
        """
        if len(tag_str) > MAX_TAG_LENGTH:
            tag_str = tag_str[0: MAX_TAG_LENGTH]

        # check if string is only alphanumeric, with '-', '_', '/', '.' or ' ' allowed with regex
        if not match(r"^[\w\-_/. ]+$", tag_str):
            raise ValueError('The tag only support alphanumeric characters, with "-", "_", "/", "." and space allowed')

        return tag_str.lower()

    def to_json(self) -> Dict:
        return {"key": self.key, "value": self.value}

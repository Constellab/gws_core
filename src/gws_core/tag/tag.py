# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from enum import Enum
from typing import List, Union

from typing_extensions import NotRequired, TypedDict

from gws_core.core.utils.date_helper import DateHelper

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

MAX_TAG_LENGTH = 1000

TagValueType = Union[str, int, float, datetime]


# Origin of the tag (who created the tag)
# If USER, the origin_id is the user id
# If EXTERNAL_SOURCE, the origin_id is the external source id
# If TASK, (when the task tagged the resource object directly) the origin_id is task model id
# If TASK_PROPAGATED, the origin_id is task model id that propagated the tag
# If EXP_PROPAGATED, the origin_id is experiment model id that propagated the tag
# If RESOURCE_PROPAGATED, the origin_id is resource model id that propagated the tag
class TagOriginType(Enum):
    USER = 'USER'
    EXTERNAL_SOURCE = 'EXTERNAL_SOURCE'
    TASK = 'TASK'
    TASK_PROPAGATED = 'TASK_PROPAGATED'
    EXPERIMENT_PROPAGATED = 'EXPERIMENT_PROPAGATED'
    RESOURCE_PROPAGATED = 'RESOURCE_PROPAGATED'


class TagDict(TypedDict):
    key: str
    value: str
    is_propagable: NotRequired[bool]
    origin_type: NotRequired[TagOriginType]
    origin_id: NotRequired[str]


class Tag():
    key: str = None
    value: TagValueType = None
    is_propagable: bool = False

    origin_type: TagOriginType = None
    origin_id: str = None

    # Do not modified, this is to know if the tag is loaded from the database in a resource
    __is_field_loaded__: bool = False

    def __init__(self, key: str, value: TagValueType, is_propagable: bool = False,
                 origin_type: TagOriginType = None, origin_id: str = None) -> None:
        self.key = self._check_parse_key(key)
        self.value = self._check_parse_value(value)
        self.is_propagable = bool(is_propagable)
        self.origin_type = origin_type
        self.origin_id = origin_id

    def set_key(self, key: str) -> None:
        self.key = self._check_parse_key(key)

    def set_value(self, value: TagValueType) -> None:
        self.value = self._check_parse_value(value)

    def get_str_value(self) -> str:
        if isinstance(self.value, datetime):
            return DateHelper.to_iso_str(self.value)
        else:
            return str(self.value)

    def _check_parse_key(self, key: str) -> str:
        if not key:
            raise ValueError('The tag key must be defined')

        return Tag.check_parse_tag_key(key)

    def _check_parse_value(self, value: TagValueType) -> TagValueType:
        # if value:
        #     value = Tag.check_parse_tag_str(value)
        return value

    def origin_is_defined(self) -> bool:
        return self.origin_type is not None and self.origin_id is not None

    def __str__(self) -> str:
        return self.key + KEY_VALUE_SEPARATOR + self.get_str_value()

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Tag):
            return False
        return (self is o) or (self.key == o.key and self.value == o.value)

    def to_json(self) -> TagDict:
        return {
            "key": self.key,
            "value": self.get_str_value(),
            "is_propagable": self.is_propagable,
            "origin_type": self.origin_type,
            "origin_id": self.origin_id
        }

    # TODO to remove once old tags are not supported
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
    def from_json(json: TagDict) -> 'Tag':
        return Tag(key=json.get("key"), value=json.get("value"),
                   is_propagable=json.get("is_propagable"),
                   origin_type=json.get("origin_type"),
                   origin_id=json.get("origin_id"))

    @staticmethod
    def check_parse_tag_key(tag_key: str) -> str:
        # TODO check what to do
        return tag_key

    @staticmethod
    def check_parse_tag_str(tag_str: TagValueType) -> TagValueType:
        """Method that check the length of the tag str (key or value) and that the tag str is valid
        """
        # TODO TO check, do this support int value ?
        return tag_str
        # if len(tag_str) > MAX_TAG_LENGTH:
        #     tag_str = tag_str[0: MAX_TAG_LENGTH]

        # # check if string is only alphanumeric, with '-', '_', '/', '.' or ' ' allowed with regex
        # if not match(r"^[\w\-_/. ]+$", tag_str):
        #     raise ValueError('The tag only support alphanumeric characters, with "-", "_", "/", "." and space allowed')

        # return tag_str.lower()

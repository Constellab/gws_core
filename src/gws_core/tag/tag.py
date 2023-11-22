# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from enum import Enum
from typing import List, Union

from typing_extensions import TypedDict

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

MAX_TAG_LENGTH = 1000

TagValueType = Union[str, int, float, datetime]


# Origin of the tag (who created the tag)
# If USER, the origin_id is the user id
# If S3, the origin_id is the external source id
# If TASK, (when the task tagged the resource object directly) the origin_id is task model id
# If TASK_PROPAGATED, the origin_id is task model id that propagated the tag
# If EXP_PROPAGATED, the origin_id is experiment model id that propagated the tag
# If RESOURCE_PROPAGATED, the origin_id is resource model id that propagated the tag
# If VIEW_PROPAGATED, the origin_id is view config id that propagated the tag
class TagOriginType(Enum):
    USER = 'USER'
    S3 = 'S3'
    TASK = 'TASK'
    TASK_PROPAGATED = 'TASK_PROPAGATED'
    EXPERIMENT_PROPAGATED = 'EXPERIMENT_PROPAGATED'
    RESOURCE_PROPAGATED = 'RESOURCE_PROPAGATED'
    VIEW_PROPAGATED = 'VIEW_PROPAGATED'


class TagOriginDict(TypedDict):
    origin_type: str
    origin_id: str


class TagDict(TypedDict):
    key: str
    value: str
    is_propagable: bool
    origins: List[TagOriginDict]


class TagOrigin():
    origin_type: TagOriginType
    origin_id: str

    def __init__(self, origin_type: TagOriginType, origin_id: str) -> None:
        self.origin_type = origin_type
        self.origin_id = origin_id

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, TagOrigin):
            return False
        return (self is o) or (self.origin_type == o.origin_type and self.origin_id == o.origin_id)

    def to_json(self) -> TagOriginDict:
        return {"origin_type": self.origin_type.value, "origin_id": self.origin_id}

    @staticmethod
    def from_json(json: TagOriginDict) -> 'TagOrigin':
        return TagOrigin(
            origin_type=StringHelper.to_enum(TagOriginType, json["origin_type"]),
            origin_id=json["origin_id"])


class TagOrigins():
    """Manage the origins of a Tag.

    Specific case: if the tag is originated by a user, we can have only one origin which is the user.
    If the tag is originated by an automatic process, we can have multiple origins.
    An automatic origin will always override a user origin.

    :return: _description_
    :rtype: _type_
    """

    _origins: List[TagOrigin]

    def __init__(self, origin_type: TagOriginType = None, origin_id: str = None) -> None:
        self._origins = []

        if origin_type and origin_id:
            self.set_origins(origin_type, origin_id)

    def add_origin(self, origin_type: TagOriginType, origin_id: str) -> bool:
        """Add an origin to the tag. Return true if the current origins have been modified
        """
        if self.has_origin(origin_type, origin_id):
            return False

        # if the current origin is user, we override it
        # an automatic origin will always override a user origin
        origin_dict: TagOrigin = TagOrigin(origin_type, origin_id)

        if self.is_empty():
            self._origins.append(TagOrigin(origin_type, origin_id))
            return True

        if self.is_user_origin():
            self._origins = [origin_dict]
        else:
            # if the current origin is automatic, we can't add a user origin
            if origin_type == TagOriginType.USER:
                return False
            self._origins.append(origin_dict)

        return True

    def add_origins(self, origins: List[TagOrigin]) -> bool:
        """Add origins to the tag. Return true if the current origins have been modified
        """

        origin_modified = False
        for origin in origins:
            modified = self.add_origin(origin.origin_type, origin.origin_id)
            origin_modified = origin_modified or modified

        return origin_modified

    def remove_origin(self, origin_type: TagOriginType, origin_id: str) -> None:
        self._origins = [origin for origin in self._origins if origin.origin_type != origin_type or
                         origin.origin_id != origin_id]

    def has_origin(self, origin_type: TagOriginType, origin_id: str) -> bool:
        return any(origin.origin_type == origin_type and origin.origin_id == origin_id for origin in self._origins)

    def get_origins(self) -> List[TagOrigin]:
        return self._origins

    def count_origins(self) -> int:
        return len(self._origins)

    def is_user_origin(self) -> bool:
        return any(origin.origin_type == TagOriginType.USER for origin in self._origins)

    def is_empty(self) -> bool:
        return len(self._origins) == 0

    def set_origins(self, origin_type: TagOriginType, origin_id: str) -> None:
        self._origins = [TagOrigin(origin_type, origin_id)]

    def to_json(self) -> List[TagOriginDict]:
        return [origin.to_json() for origin in self._origins]

    def merge_origins(self, origins: 'TagOrigins') -> bool:
        """Merge the origins of the tag with the origins of the other tag
        Return true if the current origins have been modified
        """
        return self.add_origins(origins.get_origins())

    def remove_origins(self, origins: 'TagOrigins') -> None:
        """Remove the origins of the tag with the origins of the other tag
        Return true if the current origins have been modified
        """
        for origin in origins.get_origins():
            self.remove_origin(origin.origin_type, origin.origin_id)

    @classmethod
    def from_json(cls, json: List[TagOriginDict]) -> 'TagOrigins':
        tag_origins = TagOrigins()

        if json:
            for origin in json:
                origin_obj = TagOrigin.from_json(origin)
                tag_origins.add_origin(origin_obj.origin_type, origin_obj.origin_id)
        return tag_origins


class Tag():
    key: str = None
    value: TagValueType = None
    is_propagable: bool = False

    origins: TagOrigins = None

    # Do not modified, this is to know if the tag is loaded from the database in a resource
    __is_field_loaded__: bool = False

    def __init__(self, key: str, value: TagValueType, is_propagable: bool = False,
                 origins: TagOrigins = None) -> None:
        self.key = self._check_parse_key(key)
        self.value = self._check_parse_value(value)
        self.is_propagable = bool(is_propagable)
        self.origins = origins or TagOrigins()

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
        if self.origins is None:
            return False
        return not self.origins.is_empty()

    def propagate(self, origin_type: TagOriginType, origin_id: str) -> 'Tag':
        """ Return a new instance of tag with the new origin
        """
        tag = Tag(self.key, self.value, self.is_propagable)
        tag.origins.add_origin(origin_type, origin_id)
        return tag

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
            "origins": self.origins.to_json()
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
                   origins=TagOrigins.from_json(json.get("origins")))

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

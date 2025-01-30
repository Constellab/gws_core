

import re
from datetime import datetime
from typing import List, Optional, Union

from fastapi.encoders import jsonable_encoder

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.tag.tag_dto import TagDTO, TagOriginDTO, TagOriginType

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

MAX_TAG_LENGTH = 1000

TagValueType = Union[str, int, float, datetime]


class TagOrigin():
    origin_type: TagOriginType
    origin_id: str
    # provided if the origin is an external lab
    external_lab_origin_id: Optional[str] = None

    def __init__(self, origin_type: TagOriginType, origin_id: str,
                 external_lab_origin_id: str = None) -> None:
        self.origin_type = origin_type
        self.origin_id = origin_id
        self.external_lab_origin_id = external_lab_origin_id

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, TagOrigin):
            return False
        return (self is o) or (self.origin_type == o.origin_type and self.origin_id == o.origin_id)

    def to_dto(self) -> TagOriginDTO:
        return TagOriginDTO(
            origin_type=self.origin_type,
            origin_id=self.origin_id,
            external_lab_origin_id=self.external_lab_origin_id
        )

    @staticmethod
    def from_dto(dto: TagOriginDTO) -> 'TagOrigin':
        return TagOrigin(
            origin_type=dto.origin_type,
            origin_id=dto.origin_id,
            external_lab_origin_id=dto.external_lab_origin_id)


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

    def add_origin(self, tag_origin: TagOrigin) -> bool:
        """Add an origin to the tag. Return true if the current origins have been modified
        """
        if self.has_origin(tag_origin.origin_type, tag_origin.origin_id):
            return False
        if self.is_empty():
            self._origins.append(tag_origin)
            return True

        # if the current origin is user, we override it
        # an automatic origin will always override a user origin
        if self.is_user_origin():
            self._origins = [tag_origin]
        else:
            # if the current origin is automatic, we can't add a user origin
            if tag_origin.origin_type == TagOriginType.USER:
                return False
            self._origins.append(tag_origin)

        return True

    def add_origins(self, origins: List[TagOrigin]) -> bool:
        """Add origins to the tag. Return true if the current origins have been modified
        """

        origin_modified = False
        for origin in origins:
            modified = self.add_origin(origin)
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

    def set_external_lab_origin(self, external_lab_origin_id: str) -> None:
        """Set the external lab origin for all origin if not already defined
        """
        for origin in self._origins:
            if origin.external_lab_origin_id is None:
                origin.external_lab_origin_id = external_lab_origin_id

    def to_json(self) -> List[dict]:
        return jsonable_encoder([origin for origin in self.to_dto()])

    def to_dto(self) -> List[TagOriginDTO]:
        return [origin.to_dto() for origin in self._origins]

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
    def from_dto(cls, dto: List[TagOriginDTO]) -> 'TagOrigins':
        tag_origins = TagOrigins()

        if dto:
            for origin in dto:
                tag_origin = TagOrigin.from_dto(origin)
                tag_origins.add_origin(tag_origin)
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
        self._check_key(key)
        self._check_value(value)
        self.key = key
        self.value = value
        self.is_propagable = bool(is_propagable)
        self.origins = origins or TagOrigins()

    def set_key(self, key: str) -> None:
        self.key = self._check_key(key)

    def set_value(self, value: TagValueType) -> None:
        self.value = self._check_value(value)

    def get_str_value(self) -> str:
        if isinstance(self.value, datetime):
            return DateHelper.to_iso_str(self.value)
        else:
            return str(self.value)

    def _check_key(self, key: str) -> str:
        if not key:
            raise ValueError('The tag key must be defined')

        Tag.validate_tag(key)

        return key

    def _check_value(self, value: TagValueType) -> TagValueType:
        # check that the value doesn't contains '/'
        if isinstance(value, str):
            Tag.validate_tag(value)

        return value

    def origin_is_defined(self) -> bool:
        if self.origins is None:
            return False
        return not self.origins.is_empty()

    def propagate(self, origin_type: TagOriginType, origin_id: str) -> 'Tag':
        """ Return a new instance of tag with the new origin.
        Only the origin_type and origin_id are propagated
        """
        tag = Tag(self.key, self.value, self.is_propagable)
        tag.origins.add_origin(TagOrigin(origin_type, origin_id))
        return tag

    def set_external_lab_origin(self, external_lab_origin_id: str) -> None:
        """Set the external lab origin for all origin if not already defined
        """
        self.origins.set_external_lab_origin(external_lab_origin_id)

    def __str__(self) -> str:
        return self.key + KEY_VALUE_SEPARATOR + self.get_str_value()

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Tag):
            return False
        return (self is o) or (self.key == o.key and self.value == o.value)

    def to_dto(self) -> TagDTO:
        return TagDTO(
            key=self.key,
            value=self.get_str_value(),
            is_propagable=self.is_propagable,
            origins=self.origins.to_dto()
        )

    @staticmethod
    def from_dto(dto: TagDTO) -> 'Tag':
        origins: TagOrigins = None
        if dto.origins:
            origins = TagOrigins.from_dto(dto.origins)
        return Tag(key=dto.key, value=dto.value, is_propagable=dto.is_propagable,
                   origins=origins)

    @staticmethod
    def validate_tag(tag_str: str) -> None:
        pattern = re.compile(r'^[a-z0-9\-_]+$')
        if not pattern.match(tag_str):
            raise ValueError('The tag only support alphanumeric characters in lower case, with "-", "_" allowed')

    @staticmethod
    def parse_tag(tag_str: str) -> str:
        """Parse a tag from a string
        """
        if tag_str is None:
            return None

        pattern = re.compile(r'[^a-z0-9\-_]')
        tag_str = str(tag_str).lower()
        tag_str = StringHelper.replace_accent_with_letter(tag_str)
        return pattern.sub('_', tag_str)

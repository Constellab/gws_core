import re
from datetime import datetime
from typing import Union

from fastapi.encoders import jsonable_encoder

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.tag.tag_dto import TagDTO, TagOriginDTO, TagOriginType, TagValueFormat
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

MAX_TAG_LENGTH = 1000

TagValueType = Union[str, int, float, datetime]


class TagOrigin:
    origin_type: TagOriginType
    origin_id: str
    # provided if the origin is an external lab
    external_lab_origin_id: str | None = None

    def __init__(
        self, origin_type: TagOriginType, origin_id: str, external_lab_origin_id: str = None
    ) -> None:
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
            external_lab_origin_id=self.external_lab_origin_id,
        )

    @staticmethod
    def from_dto(dto: TagOriginDTO) -> "TagOrigin":
        return TagOrigin(
            origin_type=dto.origin_type,
            origin_id=dto.origin_id,
            external_lab_origin_id=dto.external_lab_origin_id,
        )

    @staticmethod
    def current_user_origin() -> "TagOrigin":
        user_id = CurrentUserService.get_and_check_current_user().id
        return TagOrigin(origin_type=TagOriginType.USER, origin_id=user_id)

    @staticmethod
    def system_origin() -> "TagOrigin":
        """Create a tag origin for a system user"""
        return TagOrigin(
            origin_type=TagOriginType.SYSTEM, origin_id=User.get_and_check_sysuser().id
        )


class TagOrigins:
    """Manage the origins of a Tag.

    Specific case: if the tag is originated by a user, we can have only one origin which is the user.
    If the tag is originated by an automatic process, we can have multiple origins.
    An automatic origin will always override a user origin.

    :return: _description_
    :rtype: _type_
    """

    _origins: list[TagOrigin]

    def __init__(self, origin_type: TagOriginType = None, origin_id: str = None) -> None:
        self._origins = []

        if origin_type and origin_id:
            self.set_origins(origin_type, origin_id)

    def add_origin(self, tag_origin: TagOrigin) -> bool:
        """Add an origin to the tag. Return true if the current origins have been modified"""
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

    def add_origins(self, origins: list[TagOrigin]) -> bool:
        """Add origins to the tag. Return true if the current origins have been modified"""

        origin_modified = False
        for origin in origins:
            modified = self.add_origin(origin)
            origin_modified = origin_modified or modified

        return origin_modified

    def remove_origin(self, origin_type: TagOriginType, origin_id: str) -> None:
        self._origins = [
            origin
            for origin in self._origins
            if origin.origin_type != origin_type or origin.origin_id != origin_id
        ]

    def has_origin(self, origin_type: TagOriginType, origin_id: str) -> bool:
        return any(
            origin.origin_type == origin_type and origin.origin_id == origin_id
            for origin in self._origins
        )

    def get_origins(self) -> list[TagOrigin]:
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
        """Set the external lab origin for all origin if not already defined"""
        for origin in self._origins:
            if origin.external_lab_origin_id is None:
                origin.external_lab_origin_id = external_lab_origin_id

    def to_json(self) -> list[dict]:
        return jsonable_encoder([origin for origin in self.to_dto()])

    def to_dto(self) -> list[TagOriginDTO]:
        return [origin.to_dto() for origin in self._origins]

    def merge_origins(self, origins: "TagOrigins") -> bool:
        """Merge the origins of the tag with the origins of the other tag
        Return true if the current origins have been modified
        """
        return self.add_origins(origins.get_origins())

    def remove_origins(self, origins: "TagOrigins") -> None:
        """Remove the origins of the tag with the origins of the other tag
        Return true if the current origins have been modified
        """
        for origin in origins.get_origins():
            self.remove_origin(origin.origin_type, origin.origin_id)

    @classmethod
    def from_dto(cls, dto: list[TagOriginDTO]) -> "TagOrigins":
        tag_origins = TagOrigins()

        if dto:
            for origin in dto:
                tag_origin = TagOrigin.from_dto(origin)
                tag_origins.add_origin(tag_origin)
        return tag_origins

    @classmethod
    def current_user_origins(cls) -> "TagOrigins":
        tag_origins = TagOrigins()
        tag_origins.add_origin(TagOrigin.current_user_origin())
        return tag_origins

    @classmethod
    def system_origins(cls) -> "TagOrigins":
        """Create a tag origin for a system user"""
        tag_origins = TagOrigins()
        tag_origins.add_origin(TagOrigin.system_origin())
        return tag_origins


class Tag:
    key: str = None
    value: TagValueType = None
    is_propagable: bool = False

    is_community_tag_key: bool = None
    is_community_tag_value: bool = None

    additional_info: dict | None = None

    origins: TagOrigins = None

    # Do not modified, this is to know if the tag is loaded from the database in a resource
    __is_field_loaded__: bool = False

    SUPPORTED_TAG_REGEX = r"a-zA-Z0-9\-_\./"

    def __init__(
        self,
        key: str,
        value: TagValueType,
        is_propagable: bool = False,
        origins: TagOrigins = None,
        auto_parse: bool = False,
        is_community_tag_key: bool = False,
        is_community_tag_value: bool = False,
        additional_info: dict = None,
    ) -> None:
        """Create a new tag

        :param key: key of the tag
        :type key: str
        :param value: value of the tag
        :type value: TagValueType
        :param is_propagable: if True the tagwill be propagated in next resouces and views, defaults to False
        :type is_propagable: bool, optional
        :param origins: origin of the tag, defaults to None
        :type origins: TagOrigins, optional
        :param auto_parse: if True the key and value will be parsed to validate tag format.
                            if False and tag is invalid, an exception will be raised, defaults to False
        :type auto_parse: bool, optional
        """
        self.key = self._check_key(key, auto_parse)
        self.value = value
        self.is_propagable = bool(is_propagable)
        self.origins = origins or TagOrigins()
        self.is_community_tag_key = is_community_tag_key
        self.is_community_tag_value = is_community_tag_value
        self.additional_info = additional_info or {}

    def get_str_value(self) -> str:
        return Tag.convert_value_to_str(self.value)

    def _check_key(self, key: str, auto_parse: bool) -> str:
        if not key:
            raise ValueError("The tag key must be defined")

        if auto_parse:
            key = Tag.parse_tag(key)
        else:
            Tag.validate_tag(key)

        return key

    def _check_value(self, value: TagValueType, auto_parse: bool) -> TagValueType:
        if isinstance(value, str):
            if auto_parse:
                value = Tag.parse_tag(value)
            else:
                Tag.validate_tag(value)

        return value

    def origin_is_defined(self) -> bool:
        if self.origins is None:
            return False
        return not self.origins.is_empty()

    def propagate(self, origin_type: TagOriginType, origin_id: str) -> "Tag":
        """Return a new instance of tag with the new origin.
        Only the origin_type and origin_id are propagated
        """
        tag = Tag(
            self.key,
            self.value,
            self.is_propagable,
            None,
            self.is_community_tag_key,
            self.is_community_tag_value,
            self.additional_info,
        )
        tag.origins.add_origin(TagOrigin(origin_type, origin_id))
        return tag

    def set_external_lab_origin(self, external_lab_origin_id: str) -> None:
        """Set the external lab origin for all origin if not already defined"""
        self.origins.set_external_lab_origin(external_lab_origin_id)

    def get_value_format(self) -> TagValueFormat:
        if isinstance(self.value, int):
            return TagValueFormat.INTEGER
        elif isinstance(self.value, float):
            return TagValueFormat.FLOAT
        elif isinstance(self.value, datetime):
            return TagValueFormat.DATETIME
        else:
            return TagValueFormat.STRING

    def __str__(self) -> str:
        return self.key + ":" + self.get_str_value()

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Tag):
            return False
        return (self is o) or (self.key == o.key and self.value == o.value)

    def to_dto(self) -> TagDTO:
        return TagDTO(
            key=self.key,
            value=self.get_str_value(),
            is_propagable=self.is_propagable,
            origins=self.origins.to_dto(),
            value_format=self.get_value_format(),
        )

    @staticmethod
    def from_dto(dto: TagDTO) -> "Tag":
        origins: TagOrigins = None
        if dto.origins:
            origins = TagOrigins.from_dto(dto.origins)

        value = Tag.convert_str_value_to_type(dto.value, dto.value_format)
        return Tag(
            key=dto.key,
            value=value,
            is_propagable=dto.is_propagable,
            origins=origins,
            is_community_tag_key=dto.is_community_tag_key,
            is_community_tag_value=dto.is_community_tag_value,
            additional_info=dto.additional_info,
        )

    @staticmethod
    def validate_tag(tag_str: str) -> None:
        pattern = re.compile(r"^[" + Tag.SUPPORTED_TAG_REGEX + "]+$")
        if not pattern.match(tag_str):
            raise ValueError(
                'The tag only support alphanumeric characters in lower case, with "-", "_", "." and "/" allowed'
            )

    @staticmethod
    def parse_tag(tag_str: str) -> str:
        """Parse a tag from a string"""
        if tag_str is None:
            return None

        tag_str = str(tag_str).lower()
        tag_str = StringHelper.replace_accent_with_letter(tag_str)
        pattern = re.compile(r"[^" + Tag.SUPPORTED_TAG_REGEX + "]")
        return pattern.sub("_", tag_str)

    @staticmethod
    def convert_str_value_to_type(value: str, value_format: TagValueFormat) -> TagValueType:
        if value_format == TagValueFormat.INTEGER:
            return int(value)
        elif value_format == TagValueFormat.FLOAT:
            return float(value)
        elif value_format == TagValueFormat.DATETIME:
            return DateHelper.from_iso_str(value)
        else:
            return value

    @staticmethod
    def convert_value_to_str(value: TagValueType) -> str:
        if isinstance(value, datetime):
            return DateHelper.to_iso_str(value)
        else:
            return str(value)

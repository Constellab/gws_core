

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.user.user_dto import UserDTO


# Origin of the tag (who created the tag)
# If USER, the origin_id is the user id
# If S3, the origin_id is the external source id
# If TASK, (when the task tagged the resource object directly) the origin_id is task model id
# If TASK_PROPAGATED, the origin_id is task model id that propagated the tag
# If EXP_PROPAGATED, the origin_id is scenario model id that propagated the tag
# If RESOURCE_PROPAGATED, the origin_id is resource model id that propagated the tag
# If VIEW_PROPAGATED, the origin_id is view config id that propagated the tag
class TagOriginType(Enum):
    USER = 'USER'
    S3 = 'S3'
    TASK = 'TASK'
    TASK_PROPAGATED = 'TASK_PROPAGATED'
    SCENARIO_PROPAGATED = 'SCENARIO_PROPAGATED'
    RESOURCE_PROPAGATED = 'RESOURCE_PROPAGATED'
    VIEW_PROPAGATED = 'VIEW_PROPAGATED'


class TagValueFormat(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class TagOriginDTO(BaseModelDTO):
    origin_type: TagOriginType
    origin_id: str
    external_lab_origin_id: Optional[str] = None


class TagDTO(BaseModelDTO):
    key: str
    value: str
    is_propagable: Optional[bool] = None
    origins: Optional[List[TagOriginDTO]] = None
    value_format: Optional[TagValueFormat] = TagValueFormat.STRING


class TagOriginDetailDTO(TagOriginDTO):
    origin_object: Optional[str | UserDTO]


class EntityTagDTO(BaseModelDTO):
    id: str
    key: str
    value: Any
    is_user_origin: bool


class EntityTagFullDTO(EntityTagDTO):
    is_propagable: bool
    created_at: datetime
    last_modified_at: datetime


class NewTagDTO(BaseModelDTO):
    key: str
    value: str
    is_community_tag: Optional[bool] = None


class ShareTagDTO(BaseModelDTO):
    publish_mode: str
    space_selected: Optional[str] = None


class TagPropagationImpactDTO(BaseModelDTO):
    """Entity to list the entities that will be affected by the propagation of a tag
    when adding a tag to an entity manually.

    :param TypedDict: _description_
    :type TypedDict: _type_
    """
    tags: List[TagDTO]
    impacted_entities: List[EntityNavGroupDTO]


class TagKeyModelDTO(ModelDTO):
    key: str
    value_format: TagValueFormat
    is_propagable: bool
    label: Optional[str] = None
    description: Optional[RichTextDTO] = None
    deprecated: Optional[bool] = None
    is_community_tag: Optional[bool] = None
    additional_infos_specs: Optional[Dict] = None


class TagValueModelDTO(ModelDTO):
    key: str
    value: Any
    value_format: TagValueFormat
    is_community_tag_value: Optional[bool] = None
    deprecated: Optional[bool] = None
    short_description: Optional[str] = None
    additional_infos: Optional[Dict] = None


class SaveTagModelResonseDTO(BaseModelDTO):
    key_model: TagKeyModelDTO
    value_model: TagValueModelDTO


class TagKeyNotSynchronizedFields(Enum):
    """Enum to define the fields that are not synchronized with the tag service.
    This is used to avoid sending these fields to the tag service when saving a tag.
    """
    LABEL = "label"
    DESCRIPTION = "description"
    DEPRECATED = "deprecated"
    ADDITIONAL_INFOS_SPECS = "additional_infos_specs"


class TagValueNotSynchronizedFields(Enum):
    """Enum to define the fields that are not synchronized with the tag service.
    This is used to avoid sending these fields to the tag service when saving a tag.
    """
    VALUE_CREATED = "value_created"
    SHORT_DESCRIPTION = "short_description"
    ADDITIONAL_INFOS = "additional_infos"
    DEPRECATED = "deprecated"


class TagValueNotSynchronizedFieldsDTO(BaseModelDTO):
    old_value: Optional[TagValueModelDTO] = None
    new_value: TagValueModelDTO = None
    not_synchronized_fields: List[TagValueNotSynchronizedFields] = []


class TagNotSynchronizedDTO(BaseModelDTO):
    old_key: TagKeyModelDTO
    new_key: Optional[TagKeyModelDTO] = None
    not_synchronized_fields: Optional[List[TagKeyNotSynchronizedFields]] = []
    not_synchronized_values: Optional[List[TagValueNotSynchronizedFieldsDTO]] = []


class TagsNotSynchronizedDTO(BaseModelDTO):
    """DTO to define the tags that are not synchronized with the tag service.
    This is used to avoid sending these tags to the tag service when saving a tag.
    """
    tag_keys_not_synchronized: List[TagNotSynchronizedDTO] = []


class TagValueEditDTO(BaseModelDTO):
    id: Optional[str] = None
    value: Any
    short_description: Optional[str] = None
    additional_infos: Optional[Dict] = None
    tag_key: str

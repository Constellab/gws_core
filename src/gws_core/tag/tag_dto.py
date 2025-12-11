from datetime import datetime
from enum import Enum
from typing import Any, Literal

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.user.user_dto import UserDTO

ShareTagMode = Literal["PUBLIC", "SPACE"]

# Origin of the tag (who created the tag)
# If USER, the origin_id is the user id
# If S3, the origin_id is the external source id
# If TASK, (when the task tags the resource object directly) the origin_id is task model id
# If TASK_PROPAGATED, the origin_id is task model id that propagated the tag
# If EXP_PROPAGATED, the origin_id is scenario model id that propagated the tag
# If RESOURCE_PROPAGATED, the origin_id is resource model id that propagated the tag
# If VIEW_PROPAGATED, the origin_id is view config id that propagated the tag
# If SYSTEM, the origin_id is automatically set to system user id


class TagOriginType(Enum):
    USER = "USER"
    S3 = "S3"
    TASK = "TASK"
    TASK_PROPAGATED = "TASK_PROPAGATED"
    SCENARIO_PROPAGATED = "SCENARIO_PROPAGATED"
    RESOURCE_PROPAGATED = "RESOURCE_PROPAGATED"
    VIEW_PROPAGATED = "VIEW_PROPAGATED"
    SYSTEM = "SYSTEM"


class TagValueFormat(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class TagOriginDTO(BaseModelDTO):
    origin_type: TagOriginType
    origin_id: str
    external_lab_origin_id: str | None = None


class TagDTO(BaseModelDTO):
    key: str
    value: str
    is_propagable: bool = False
    origins: list[TagOriginDTO] | None = None
    value_format: TagValueFormat | None = TagValueFormat.STRING
    is_community_tag_key: bool = False
    is_community_tag_value: bool = False
    additional_info: dict | None = None


class TagOriginDetailDTO(TagOriginDTO):
    origin_object: str | UserDTO | None


class EntityTagDTO(BaseModelDTO):
    id: str
    key: str
    value: Any
    is_user_origin: bool
    is_community_tag_key: bool | None = None
    label: str | None = None


class EntityTagFullDTO(EntityTagDTO):
    is_propagable: bool
    created_at: datetime
    last_modified_at: datetime


class NewTagDTO(BaseModelDTO):
    key: str
    value: str
    is_community_tag_key: bool | None = None
    is_community_tag_value: bool | None = None
    additional_info: dict | None = None


class ShareTagDTO(BaseModelDTO):
    publish_mode: ShareTagMode
    space_selected: str | None = None


class TagPropagationImpactDTO(BaseModelDTO):
    """Entity to list the entities that will be affected by the propagation of a tag
    when adding a tag to an entity manually.

    :param TypedDict: _description_
    :type TypedDict: _type_
    """

    tags: list[TagDTO]
    impacted_entities: list[EntityNavGroupDTO]


class TagKeyModelCreateDTO(BaseModelDTO):
    key: str
    label: str


class TagKeyModelDTO(ModelDTO):
    key: str
    value_format: TagValueFormat
    label: str | None = None
    description: RichTextDTO | None = None
    deprecated: bool | None = None
    is_community_tag: bool | None = None
    additional_infos_specs: dict | None = None


class TagValueModelDTO(ModelDTO):
    key: str
    value: Any
    value_format: TagValueFormat
    is_community_tag_value: bool | None = None
    deprecated: bool | None = None
    short_description: str | None = None
    additional_infos: dict | None = None


class SaveTagModelResonseDTO(BaseModelDTO):
    key_model: TagKeyModelDTO
    value_model: TagValueModelDTO


class TagKeyNotSynchronizedFields(Enum):
    """Enum to define the fields that are not synchronized with the tag service.
    This is used to avoid sending these fields to the tag service when saving a tag.
    """

    LABEL = "label_modified"
    DESCRIPTION = "description_modified"
    DEPRECATED = "deprecated"
    ADDITIONAL_INFOS_SPECS = "additional_info_specs_modified"


class TagValueNotSynchronizedFields(Enum):
    """Enum to define the fields that are not synchronized with the tag service.
    This is used to avoid sending these fields to the tag service when saving a tag.
    """

    VALUE_CREATED = "value_created"
    SHORT_DESCRIPTION = "short_description_modified"
    ADDITIONAL_INFOS = "additional_info_modified"
    DEPRECATED = "deprecated"


class TagValueNotSynchronizedFieldsDTO(BaseModelDTO):
    old_value: TagValueModelDTO | None = None
    new_value: TagValueModelDTO = None
    not_synchronized_fields: list[TagValueNotSynchronizedFields] = []


class TagNotSynchronizedDTO(BaseModelDTO):
    old_key: TagKeyModelDTO
    new_key: TagKeyModelDTO | None = None
    not_synchronized_fields: list[TagKeyNotSynchronizedFields] | None = []
    not_synchronized_values: list[TagValueNotSynchronizedFieldsDTO] | None = []


class TagsNotSynchronizedDTO(BaseModelDTO):
    """DTO to define the tags that are not synchronized with the tag service.
    This is used to avoid sending these tags to the tag service when saving a tag.
    """

    tag_keys_not_synchronized: list[TagNotSynchronizedDTO] = []


class TagValueEditDTO(BaseModelDTO):
    id: str | None = None
    value: Any
    short_description: str | None = None
    additional_infos: dict | None = None
    tag_key: str

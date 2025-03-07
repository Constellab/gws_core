

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO
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


class TagValueModelDTO(ModelDTO):
    key: str
    value: Any
    value_format: TagValueFormat


class SaveTagModelResonseDTO(BaseModelDTO):
    key_model: TagKeyModelDTO
    value_model: TagValueModelDTO

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import Any, List

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO


class TagDTO(BaseModelDTO):
    key: str
    value: Any
    is_user_origin: bool
    is_propagable: bool


class TagOriginDTO(BaseModelDTO):
    origin_type: str
    origin_id: str


class EntityTagDTO(BaseModelDTO):
    id: str
    key: str
    value: Any
    is_user_origin: bool


class EntityTagFullDTO(EntityTagDTO):
    is_propagable: bool
    origins: List[TagOriginDTO]
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
    # TODO type with EntityTagValueFormat
    value_format: Any
    is_propagable: bool


class TagValueModelDTO(ModelDTO):
    key: str
    value: Any
    # TODO type with EntityTagValueFormat
    value_format: Any


class SaveTagModelResonseDTO(BaseModelDTO):
    key_model: TagKeyModelDTO
    value_model: TagValueModelDTO

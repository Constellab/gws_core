# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from typing_extensions import TypedDict

from gws_core.entity_navigator.entity_navigator_type import EntityNavGroup
from gws_core.tag.tag import Tag


class NewTagDTO(TypedDict):
    key: str
    value: str


class TagPropagationImpactDTO():
    """Entity to list the entities that will be affected by the propagation of a tag
    when adding a tag to an entity manually.

    :param TypedDict: _description_
    :type TypedDict: _type_
    """
    tags: List[Tag]
    impacted_entities: List[EntityNavGroup]

    def __init__(self, tags: List[Tag], impacted_entities: List[EntityNavGroup]) -> None:
        self.tags = tags
        self.impacted_entities = impacted_entities

    def to_json(self):
        return {
            'tags': [tag.to_json() for tag in self.tags],
            'impacted_entities': self.impacted_entities

        }

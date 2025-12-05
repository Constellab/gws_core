from abc import abstractmethod
from enum import Enum
from typing import Any

from gws_core.core.model.model_dto import BaseModelDTO


class NavigableEntityType(Enum):
    """Enum that represent entity that can be navigated in the system."""

    SCENARIO = "SCENARIO"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    NOTE = "NOTE"

    def get_human_name(self, capitalize: bool = False, plurial: bool = False) -> str:
        human_name: str = None
        if self == NavigableEntityType.SCENARIO:
            human_name = "Scenario"
        elif self == NavigableEntityType.RESOURCE:
            human_name = "Resource"
        elif self == NavigableEntityType.VIEW:
            human_name = "View"
        elif self == NavigableEntityType.NOTE:
            human_name = "Note"
        else:
            human_name = "Unknown"

        if capitalize:
            human_name = human_name.capitalize()
        if plurial:
            human_name += "s"
        return human_name

    def convert_to_tag_entity_type(self) -> "TagEntityType":
        from gws_core.tag.tag_entity_type import TagEntityType

        if self == NavigableEntityType.SCENARIO:
            return TagEntityType.SCENARIO
        elif self == NavigableEntityType.RESOURCE:
            return TagEntityType.RESOURCE
        elif self == NavigableEntityType.VIEW:
            return TagEntityType.VIEW
        elif self == NavigableEntityType.NOTE:
            return TagEntityType.NOTE
        else:
            raise Exception(
                f"The navigable entity type {self} does not have a tag entity type corresponding to it"
            )


class NavigableEntity:
    id: str

    @abstractmethod
    def get_navigable_entity_type(self) -> NavigableEntityType:
        pass

    @abstractmethod
    def get_navigable_entity_name(self) -> str:
        pass

    def navigable_entity_is_validated(self) -> bool:
        return False

    def to_dto(self) -> BaseModelDTO:
        pass


class EntityNavGroupDTO(BaseModelDTO):
    """Store the entities nav grouped by type"""

    type: NavigableEntityType
    entities: list[Any]

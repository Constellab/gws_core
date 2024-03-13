

from abc import abstractmethod
from enum import Enum
from typing import Any, List, TypeVar

from gws_core.core.model.model_dto import BaseModelDTO


class EntityType(Enum):
    EXPERIMENT = "EXPERIMENT"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    REPORT = "REPORT"
    PROTOCOL_TEMPLATE = 'PROTOCOL_TEMPLATE'
    PROJECT = 'PROJECT'

    @staticmethod
    def get_human_name(entity_type: 'EntityType', capitalize: bool = False, plurial: bool = False) -> str:
        human_name: str = None
        if entity_type == EntityType.EXPERIMENT:
            human_name = 'Experiment'
        elif entity_type == EntityType.RESOURCE:
            human_name = 'Resource'
        elif entity_type == EntityType.VIEW:
            human_name = 'View'
        elif entity_type == EntityType.REPORT:
            human_name = 'Report'
        elif entity_type == EntityType.PROTOCOL_TEMPLATE:
            human_name = 'Protocol Template'
        elif entity_type == EntityType.PROJECT:
            human_name = 'Project'
        else:
            human_name = 'Unknown'

        if capitalize:
            human_name = human_name.capitalize()
        if plurial:
            human_name += 's'

        return human_name


all_entity_types = [EntityType.EXPERIMENT, EntityType.RESOURCE,
                    EntityType.VIEW, EntityType.REPORT]


class NavigableEntity():

    id: str

    @abstractmethod
    def get_entity_type(self) -> EntityType:
        pass

    @abstractmethod
    def get_entity_name(self) -> str:
        pass

    def entity_is_validated(self) -> bool:
        return False

    def to_dto(self) -> BaseModelDTO:
        pass


class EntityNavGroupDTO(BaseModelDTO):
    """Store the entities nav grouped by type
    """
    type: EntityType
    entities: List[Any]


GenericNavigableEntity = TypeVar('GenericNavigableEntity', bound=NavigableEntity)

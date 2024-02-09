# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar, Union

from pyparsing import Set

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


class EntityNavDTO(BaseModelDTO):
    id: str
    type: EntityType
    name: str
    parent_name: Optional[str]
    parent_type: Optional[EntityType]


class EntityNavGroupDTO(BaseModelDTO):
    """Store the entities nav grouped by type
    """
    type: EntityType
    entities: List[Any]


class NavigableEntity():

    id: str

    def get_entity_nav(self) -> EntityNavDTO:
        return EntityNavDTO(
            id=self.id,
            type=self.get_entity_type(),
            name=self.get_entity_name(),
            parent_name=self.get_entity_parent_name(),
            parent_type=self.get_entity_parent_type()
        )

    @abstractmethod
    def get_entity_type(self) -> EntityType:
        pass

    @abstractmethod
    def get_entity_name(self) -> str:
        pass

    def get_entity_parent_name(self) -> Optional[str]:
        return None

    def get_entity_parent_type(self) -> Optional[EntityType]:
        return None

    def entity_is_validated(self) -> bool:
        return False

    def to_dto(self) -> BaseModelDTO:
        pass


GenericNavigableEntity = TypeVar('GenericNavigableEntity', bound=NavigableEntity)


class NavigableEntitySet(Generic[GenericNavigableEntity]):

    _entities: Set[GenericNavigableEntity]

    def __init__(
            self, entities:
            Union[GenericNavigableEntity, List[GenericNavigableEntity],
                  Set[GenericNavigableEntity]] = None):
        if entities is None:
            self._entities = set()
        elif isinstance(entities, list):
            self._entities = set(entities)
        elif isinstance(entities, set):
            self._entities = entities
        else:
            self._entities = set([entities])

    def get_entity_navs(self) -> List[BaseModelDTO]:
        return [entity.to_dto() for entity in self._entities]

    def get_entity_dict_nav_group(self) -> List[EntityNavGroupDTO]:
        entity_nav_group: List[EntityNavGroupDTO] = []
        for entity_type in EntityType:
            group_dto = EntityNavGroupDTO(
                type=entity_type,
                entities=[entity.to_dto() for entity in self._entities
                          if entity.get_entity_type() == entity_type])
            entity_nav_group.append(group_dto)
        return entity_nav_group

    def get_entity_ids(self) -> List[str]:
        return [entity.id for entity in self._entities]

    def get_as_set(self) -> Set[GenericNavigableEntity]:
        return set(self._entities)

    def get_as_list(self) -> List[GenericNavigableEntity]:
        return list(self._entities)

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.get_entity_ids()

    def has_entity_of_type(self, entity_type: EntityType) -> bool:
        return len(self.get_entity_by_type(entity_type)) > 0

    def get_entity_by_type(self, entity_type: EntityType) -> List[GenericNavigableEntity]:
        return [entity for entity in self._entities if entity.get_entity_type() == entity_type]

    def __len__(self):
        return len(self._entities)

    def __iter__(self):
        return iter(self._entities)

    def is_empty(self):
        return len(self._entities) == 0

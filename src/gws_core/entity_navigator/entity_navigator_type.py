# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from enum import Enum
from typing import Generic, List, TypeVar, Union

from pyparsing import Set
from typing_extensions import TypedDict


class EntityType(Enum):
    EXPERIMENT = "EXPERIMENT"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    REPORT = "REPORT"
    PROTOCOL_TEMPLATE = 'PROTOCOL_TEMPLATE'


all_entity_types = [EntityType.EXPERIMENT, EntityType.RESOURCE,
                    EntityType.VIEW, EntityType.REPORT]


class EntityNav(TypedDict):
    id: str
    type: EntityType
    name: str


class EntityNavGroup(TypedDict):
    type: EntityType
    entities: List[EntityNav]


class NavigableEntity():

    id: str

    def get_entity_nav(self) -> EntityNav:
        return {
            'id': self.id,
            'type': self.get_entity_type(),
            'name': self.get_entity_name()
        }

    @abstractmethod
    def get_entity_type(self) -> EntityType:
        pass

    @abstractmethod
    def get_entity_name(self) -> str:
        pass


GenericNavigableEntity = TypeVar('GenericNavigableEntity', bound=NavigableEntity)


class NavigableEntitySet(Generic[GenericNavigableEntity]):

    _entities: Set[GenericNavigableEntity]

    def __init__(
            self, entities:
            Union[GenericNavigableEntity, List[GenericNavigableEntity],
                  Set[GenericNavigableEntity]] = None):
        if isinstance(entities, list):
            self._entities = set(entities)
        elif isinstance(entities, set):
            self._entities = entities
        else:
            self._entities = set([entities])

    def get_entity_navs(self) -> List[EntityNav]:
        return [entity.get_entity_nav() for entity in self._entities]

    def get_entity_dict_nav_group(self) -> List[EntityNavGroup]:
        entity_nav_group: List[EntityNavGroup] = []
        for entity_type in EntityType:
            entity_nav_group.append({'type': entity_type, 'entities': [entity.get_entity_nav(
            ) for entity in self._entities if entity.get_entity_type() == entity_type]})
        return entity_nav_group

    def get_entity_ids(self) -> List[str]:
        return [entity.id for entity in self._entities]

    def get_as_set(self) -> Set[GenericNavigableEntity]:
        return set(self._entities)

    def get_as_list(self) -> List[GenericNavigableEntity]:
        return list(self._entities)

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.get_entity_ids()

    def __len__(self):
        return len(self._entities)

    def __iter__(self):
        return iter(self._entities)

    def is_empty(self):
        return len(self._entities) == 0
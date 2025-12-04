from typing import Iterable, List, Set, Union

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.entity_navigator.entity_navigator_type import (
    EntityNavGroupDTO,
    NavigableEntity,
    NavigableEntityType,
)


class NavigableEntityDeep(BaseModelDTO):
    """Store an entity with its deep level in the navigation tree"""

    entity: NavigableEntity
    deep_level: int

    class Config:
        arbitrary_types_allowed = True

    def __hash__(self) -> int:
        return self.entity.__hash__()

    def get_entity_type(self) -> NavigableEntityType:
        return self.entity.get_navigable_entity_type()

    def to_entity_dto(self) -> BaseModelDTO:
        return self.entity.to_dto()


class NavigableEntitySet:
    """Store a set of entities with their deep level in the navigation tree"""

    _entities: Set[NavigableEntityDeep]

    def __init__(
        self,
        entities: Union[NavigableEntity, Iterable[NavigableEntity]] = None,
        deep_level: int = 0,
    ):
        self._entities = set()

        if isinstance(entities, Iterable):
            self.update(entities, deep_level)
        else:
            self.add(entities, deep_level)

    def get_entity_navs(self) -> List[BaseModelDTO]:
        return [entity.to_entity_dto() for entity in self._entities]

    def get_entity_dict_nav_group(self) -> List[EntityNavGroupDTO]:
        entity_nav_group: List[EntityNavGroupDTO] = []
        for entity_type in NavigableEntityType:
            group_dto = EntityNavGroupDTO(
                type=entity_type,
                entities=[
                    entity.to_entity_dto()
                    for entity in self._entities
                    if entity.get_entity_type() == entity_type
                ],
            )
            entity_nav_group.append(group_dto)
        return entity_nav_group

    def get_entity_ids(self) -> List[str]:
        return [entity.entity.id for entity in self._entities]

    def get_as_set(self) -> Set[NavigableEntityDeep]:
        return set(self._entities)

    def get_entities(self) -> Set[NavigableEntity]:
        return set([entity.entity for entity in self._entities])

    def get_as_list(self) -> List[NavigableEntityDeep]:
        return list(self._entities)

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.get_entity_ids()

    def has_entity_of_type(self, entity_type: NavigableEntityType) -> bool:
        return len(self.get_entity_deep_by_type(entity_type)) > 0

    def get_entity_deep_by_type(
        self, entity_type: NavigableEntityType
    ) -> List[NavigableEntityDeep]:
        return [entity for entity in self._entities if entity.get_entity_type() == entity_type]

    def get_entity_by_type(self, entity_type: NavigableEntityType) -> List[NavigableEntity]:
        return [
            entity.entity for entity in self._entities if entity.get_entity_type() == entity_type
        ]

    def add(self, entity: NavigableEntity, deep_level: int = 0):
        self._entities.add(NavigableEntityDeep(entity=entity, deep_level=deep_level))

    def update(self, entity: Iterable[NavigableEntity], deep_level: int = 0):
        for e in entity:
            self.add(e, deep_level)

    def remove(self, entity: Iterable[NavigableEntity]):
        self._entities = self._entities - entity

    def remove_deep(self, deep_level: int):
        self._entities = set(
            [entity for entity in self._entities if entity.deep_level != deep_level]
        )

    def get_entities_from_deepest_level(
        self, entity_type: NavigableEntityType
    ) -> List[NavigableEntity]:
        """Return the entities order from the highest deep level to the lowest"""
        entities_deep = sorted(
            self.get_entity_deep_by_type(entity_type), key=lambda x: x.deep_level, reverse=True
        )
        return [entity.entity for entity in entities_deep]

    def __len__(self):
        return len(self._entities)

    def __iter__(self):
        return iter(self._entities)

    def is_empty(self):
        return len(self._entities) == 0

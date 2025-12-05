
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO


class ImpactResultDTO(BaseModelDTO):
    has_entities: bool
    impacted_entities: list[EntityNavGroupDTO]


class ImpactResult:
    impacted_entities: NavigableEntitySet

    def __init__(self, impacted_entities: NavigableEntitySet):
        self.impacted_entities = impacted_entities

    def has_entities(self) -> bool:
        return len(self.impacted_entities) > 0

    def to_dto(self) -> ImpactResultDTO:
        return ImpactResultDTO(
            has_entities=self.has_entities(),
            impacted_entities=self.impacted_entities.get_entity_dict_nav_group(),
        )

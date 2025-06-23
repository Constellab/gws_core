

from abc import abstractmethod
from enum import Enum
from typing import Any, List, Type, TypeVar

from gws_core.core.model.model import Model
from gws_core.core.model.model_dto import BaseModelDTO


class EntityType(Enum):
    SCENARIO = "SCENARIO"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    NOTE = "NOTE"
    SCENARIO_TEMPLATE = 'SCENARIO_TEMPLATE'
    FOLDER = 'FOLDER'
    TAG = 'TAG'

    @staticmethod
    def get_human_name(entity_type: 'EntityType', capitalize: bool = False, plurial: bool = False) -> str:
        human_name: str = None
        if entity_type == EntityType.SCENARIO:
            human_name = 'Scenario'
        elif entity_type == EntityType.RESOURCE:
            human_name = 'Resource'
        elif entity_type == EntityType.VIEW:
            human_name = 'View'
        elif entity_type == EntityType.NOTE:
            human_name = 'Note'
        elif entity_type == EntityType.SCENARIO_TEMPLATE:
            human_name = 'Scenario template'
        elif entity_type == EntityType.FOLDER:
            human_name = 'Folder'
        elif entity_type == EntityType.TAG:
            human_name = 'Tag'
        else:
            human_name = 'Unknown'

        if capitalize:
            human_name = human_name.capitalize()
        if plurial:
            human_name += 's'

        return human_name

    @staticmethod
    def get_entity_model_type(entity_type: 'EntityType') -> Type[Model]:
        from gws_core.folder.space_folder import SpaceFolder
        from gws_core.note.note import Note
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.resource.view_config.view_config import ViewConfig
        from gws_core.scenario.scenario import Scenario
        from gws_core.scenario_template.scenario_template import \
            ScenarioTemplate
        from gws_core.tag.tag_key_model import TagKeyModel
        if entity_type == EntityType.SCENARIO:
            return Scenario
        elif entity_type == EntityType.RESOURCE:
            return ResourceModel
        elif entity_type == EntityType.VIEW:
            return ViewConfig
        elif entity_type == EntityType.NOTE:
            return Note
        elif entity_type == EntityType.SCENARIO_TEMPLATE:
            return ScenarioTemplate
        elif entity_type == EntityType.FOLDER:
            return SpaceFolder
        elif entity_type == EntityType.TAG:
            return TagKeyModel

        raise Exception(f"Unknown entity type {entity_type}")


all_entity_types = [EntityType.SCENARIO, EntityType.RESOURCE,
                    EntityType.VIEW, EntityType.NOTE, EntityType.TAG]


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

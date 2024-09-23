

from abc import abstractmethod
from enum import Enum
from typing import Any, List, Type, TypeVar

from gws_core.core.model.model import Model
from gws_core.core.model.model_dto import BaseModelDTO


class EntityType(Enum):
    EXPERIMENT = "EXPERIMENT"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    NOTE = "NOTE"
    PROTOCOL_TEMPLATE = 'PROTOCOL_TEMPLATE'
    FOLDER = 'FOLDER'

    @staticmethod
    def get_human_name(entity_type: 'EntityType', capitalize: bool = False, plurial: bool = False) -> str:
        human_name: str = None
        if entity_type == EntityType.EXPERIMENT:
            human_name = 'Experiment'
        elif entity_type == EntityType.RESOURCE:
            human_name = 'Resource'
        elif entity_type == EntityType.VIEW:
            human_name = 'View'
        elif entity_type == EntityType.NOTE:
            human_name = 'Note'
        elif entity_type == EntityType.PROTOCOL_TEMPLATE:
            human_name = 'Protocol Template'
        elif entity_type == EntityType.FOLDER:
            human_name = 'Folder'
        else:
            human_name = 'Unknown'

        if capitalize:
            human_name = human_name.capitalize()
        if plurial:
            human_name += 's'

        return human_name

    @staticmethod
    def get_entity_model_type(entity_type: 'EntityType') -> Type[Model]:
        from gws_core.experiment.experiment import Experiment
        from gws_core.folder.space_folder import SpaceFolder
        from gws_core.note.note import Note
        from gws_core.protocol_template.protocol_template import \
            ProtocolTemplate
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.resource.view_config.view_config import ViewConfig
        if entity_type == EntityType.EXPERIMENT:
            return Experiment
        elif entity_type == EntityType.RESOURCE:
            return ResourceModel
        elif entity_type == EntityType.VIEW:
            return ViewConfig
        elif entity_type == EntityType.NOTE:
            return Note
        elif entity_type == EntityType.PROTOCOL_TEMPLATE:
            return ProtocolTemplate
        elif entity_type == EntityType.FOLDER:
            return SpaceFolder

        raise Exception(f"Unknown entity type {entity_type}")


all_entity_types = [EntityType.EXPERIMENT, EntityType.RESOURCE,
                    EntityType.VIEW, EntityType.NOTE]


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

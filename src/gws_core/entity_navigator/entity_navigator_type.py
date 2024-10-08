

from abc import abstractmethod
from enum import Enum
from typing import Any, List, Type, TypeVar

from gws_core.core.model.model import Model
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

    @staticmethod
    def get_entity_model_type(entity_type: 'EntityType') -> Type[Model]:
        from gws_core.experiment.experiment import Experiment
        from gws_core.project.project import Project
        from gws_core.protocol_template.protocol_template import \
            ProtocolTemplate
        from gws_core.report.report import Report
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.resource.view_config.view_config import ViewConfig
        if entity_type == EntityType.EXPERIMENT:
            return Experiment
        elif entity_type == EntityType.RESOURCE:
            return ResourceModel
        elif entity_type == EntityType.VIEW:
            return ViewConfig
        elif entity_type == EntityType.REPORT:
            return Report
        elif entity_type == EntityType.PROTOCOL_TEMPLATE:
            return ProtocolTemplate
        elif entity_type == EntityType.PROJECT:
            return Project

        raise Exception(f"Unknown entity type {entity_type}")


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

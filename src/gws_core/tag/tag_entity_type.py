from enum import Enum
from typing import Type

from gws_core.core.model.model import Model
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType


class TagEntityType(Enum):
    """Enum that represents the type of entity that can be tagged."""

    SCENARIO = "SCENARIO"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    NOTE = "NOTE"
    SCENARIO_TEMPLATE = "SCENARIO_TEMPLATE"

    def get_entity_model_type(self) -> Type[Model]:
        from gws_core.note.note import Note
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.resource.view_config.view_config import ViewConfig
        from gws_core.scenario.scenario import Scenario
        from gws_core.scenario_template.scenario_template import ScenarioTemplate

        if self == TagEntityType.SCENARIO:
            return Scenario
        elif self == TagEntityType.RESOURCE:
            return ResourceModel
        elif self == TagEntityType.VIEW:
            return ViewConfig
        elif self == TagEntityType.NOTE:
            return Note
        elif self == TagEntityType.SCENARIO_TEMPLATE:
            return ScenarioTemplate

        raise Exception(f"Unknown entity type {self}")

    def convert_to_navigable_entity_type(self) -> NavigableEntityType:
        if self == TagEntityType.SCENARIO:
            return NavigableEntityType.SCENARIO
        elif self == TagEntityType.RESOURCE:
            return NavigableEntityType.RESOURCE
        elif self == TagEntityType.VIEW:
            return NavigableEntityType.VIEW
        elif self == TagEntityType.NOTE:
            return NavigableEntityType.NOTE
        else:
            raise Exception(
                f"The tag entity type {self} does not have a navigable entity type corresponding to it"
            )

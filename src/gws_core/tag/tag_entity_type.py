from enum import Enum

from gws_core.core.model.model import Model
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType


class TagEntityType(Enum):
    """Enum that represents the type of entity that can be tagged."""

    SCENARIO = "SCENARIO"
    RESOURCE = "RESOURCE"
    VIEW = "VIEW"
    NOTE = "NOTE"
    SCENARIO_TEMPLATE = "SCENARIO_TEMPLATE"
    NOTE_TEMPLATE = "NOTE_TEMPLATE"
    FORM_TEMPLATE = "FORM_TEMPLATE"
    FORM = "FORM"

    def get_entity_model_type(self) -> type[Model]:
        from gws_core.form.form import Form
        from gws_core.form_template.form_template import FormTemplate
        from gws_core.note.note import Note
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.resource.view_config.view_config import ViewConfig
        from gws_core.scenario.scenario import Scenario
        from gws_core.note_template.note_template import NoteTemplate
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
        elif self == TagEntityType.NOTE_TEMPLATE:
            return NoteTemplate
        elif self == TagEntityType.FORM_TEMPLATE:
            return FormTemplate
        elif self == TagEntityType.FORM:
            return Form

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
        elif self == TagEntityType.FORM_TEMPLATE:
            return NavigableEntityType.FORM_TEMPLATE
        elif self == TagEntityType.FORM:
            return NavigableEntityType.FORM
        else:
            raise Exception(
                f"The tag entity type {self} does not have a navigable entity type corresponding to it"
            )

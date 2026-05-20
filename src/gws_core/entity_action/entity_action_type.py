from enum import Enum

from gws_core.core.model.model import Model
from gws_core.tag.tag_entity_type import TagEntityType


class EntityActionType(Enum):
    """Enum of the lab entities that support the entity action plugin system.

    It is intentionally separate from :class:`TagEntityType` so that the set of
    "actionable" entities can diverge from the set of "taggable" entities. It
    still bridges to ``TagEntityType`` to reuse the entity -> model mapping.
    """

    SCENARIO = "SCENARIO"
    RESOURCE = "RESOURCE"
    NOTE = "NOTE"
    FORM = "FORM"
    SCENARIO_TEMPLATE = "SCENARIO_TEMPLATE"
    NOTE_TEMPLATE = "NOTE_TEMPLATE"
    FORM_TEMPLATE = "FORM_TEMPLATE"

    def to_tag_entity_type(self) -> TagEntityType:
        """Return the matching TagEntityType (names are kept identical)."""
        return TagEntityType[self.name]

    def get_entity_model_type(self) -> type[Model]:
        """Return the model class backing this entity type."""
        return self.to_tag_entity_type().get_entity_model_type()

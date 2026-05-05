from enum import Enum
from typing import Any

from gws_core.core.model.model_dto import BaseModelDTO


class ConfigChangeAction(Enum):
    FIELD_CREATED = "FIELD_CREATED"
    FIELD_UPDATED = "FIELD_UPDATED"
    FIELD_DELETED = "FIELD_DELETED"
    PARAMSET_ITEM_ADDED = "PARAMSET_ITEM_ADDED"
    PARAMSET_ITEM_REMOVED = "PARAMSET_ITEM_REMOVED"


class ConfigChangeEntry(BaseModelDTO):
    """One change produced by ConfigSpecs.diff_values comparing two values dicts.

    Generic across any ConfigSpecs consumer (forms, tasks, views). Form-specific
    workflow events (e.g. status transitions) live in FormChangeEntry, which
    subclasses this and adds form-only actions to its enum.
    """

    field_path: str
    action: ConfigChangeAction
    old_value: Any | None = None
    new_value: Any | None = None

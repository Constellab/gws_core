from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.user.user_dto import UserDTO


class FormStatus(Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class FormChangeAction(Enum):
    FIELD_CREATED = "FIELD_CREATED"
    FIELD_UPDATED = "FIELD_UPDATED"
    FIELD_DELETED = "FIELD_DELETED"
    PARAMSET_ITEM_ADDED = "PARAMSET_ITEM_ADDED"
    PARAMSET_ITEM_REMOVED = "PARAMSET_ITEM_REMOVED"
    STATUS_CHANGED = "STATUS_CHANGED"


class FormChangeEntry(BaseModelDTO):
    """One change inside a FormSaveEvent.changes list. See form_feature.md §3.4."""

    field_path: str
    action: FormChangeAction
    old_value: Any | None = None
    new_value: Any | None = None


class FormDTO(ModelWithUserDTO):
    name: str
    template_version_id: str
    status: FormStatus
    submitted_at: datetime | None
    submitted_by: UserDTO | None
    is_archived: bool


class FormFullDTO(FormDTO):
    values: dict[str, Any] | None


class FormSaveEventDTO(ModelDTO):
    form_id: str
    user: UserDTO
    changes: list[FormChangeEntry]

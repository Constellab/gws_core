from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.user.user_dto import UserDTO


class FormStatus(Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class FormChangeAction(Enum):
    """Form-specific change actions. The first five members mirror
    ``ConfigChangeAction`` by string value — persisted JSON in
    ``FormSaveEvent.changes`` is identical regardless of which enum the
    Python value came from. ``STATUS_CHANGED`` is form-only (it tracks the
    DRAFT→SUBMITTED workflow transition, not a value diff).
    """

    FIELD_CREATED = ConfigChangeAction.FIELD_CREATED.value
    FIELD_UPDATED = ConfigChangeAction.FIELD_UPDATED.value
    FIELD_DELETED = ConfigChangeAction.FIELD_DELETED.value
    PARAMSET_ITEM_ADDED = ConfigChangeAction.PARAMSET_ITEM_ADDED.value
    PARAMSET_ITEM_REMOVED = ConfigChangeAction.PARAMSET_ITEM_REMOVED.value
    STATUS_CHANGED = "STATUS_CHANGED"


class FormChangeEntry(ConfigChangeEntry):
    """One change inside a FormSaveEvent.changes list. See form_feature.md §3.4.

    Inherits ``field_path``, ``old_value``, ``new_value`` from
    ``ConfigChangeEntry``; widens ``action`` to allow form-only members
    (``STATUS_CHANGED``).
    """

    action: FormChangeAction


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


class CreateFormDTO(BaseModelDTO):
    template_version_id: str
    name: str | None = None


class UpdateFormDTO(BaseModelDTO):
    name: str | None = None


class SaveFormDTO(BaseModelDTO):
    values: dict[str, Any]
    name: str | None = None
    status_transition: FormStatus | None = None


class FormSaveResultDTO(BaseModelDTO):
    """Result of a form save / submit / read.

    `form.values` is the union of user-input values and computed values
    (see form_feature.md §6.7). `errors` carries per-computed-field error
    messages keyed by spec key (or `<paramset_key>[].<field>` for per-row).
    """

    form: FormFullDTO
    errors: dict[str, str]

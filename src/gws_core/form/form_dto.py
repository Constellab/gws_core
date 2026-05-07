from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.param.param_types import ParamSpecDTO
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


class FormTemplateRefDTO(BaseModelDTO):
    """Lightweight reference to a Form's pinned FormTemplateVersion.

    Carries just enough to display the source template (e.g. a "My Form
    (v3)" header) without a separate fetch. For the full template or
    version content, hit the form_template endpoints.
    """

    template_id: str
    template_name: str
    version_id: str
    version_number: int


class FormDTO(ModelWithUserDTO):
    name: str
    template: FormTemplateRefDTO
    status: FormStatus
    submitted_at: datetime | None
    submitted_by: UserDTO | None
    is_archived: bool


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


class ComputedParamValueDTO(BaseModelDTO):
    """Wire shape for a single ComputedParam cell in a save/read response.

    Wraps the evaluated scalar with its per-cell error message so the client
    can render value + error inline without consulting a separate errors
    map. ``errors`` is None on success, a human-readable string on failure
    (in which case ``value`` is None).
    """

    value: Any
    errors: str | None


class FormSaveResultDTO(BaseModelDTO):
    """Renderable content of a form (returned by save / submit / get-content).

    Carries only the data needed to render and edit the form — no Form
    record metadata. Clients that need status/submitted_at/etc. should
    call ``GET /form/{id_}`` separately.

    `values` is the union of user-input values and computed values (see
    form_feature.md §6.7). User-input cells carry the raw scalar; computed
    cells carry a ``ComputedParamValueDTO``-shaped dict ``{"value", "errors"}``
    inline (outer-scope keys and per-row ParamSet cells alike). `specs` is
    the form's ConfigSpecs serialized so the client can render fields
    without a separate template fetch.
    """

    values: dict[str, Any] | None
    specs: dict[str, ParamSpecDTO]

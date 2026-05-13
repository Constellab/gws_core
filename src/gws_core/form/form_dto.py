from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.user.user_dto import UserDTO


@dataclass
class FormValidationResult:
    """Outcome of :meth:`FormService.validate_values_against_specs`.

    ``values`` is the validated + computed-merged union dict (invalid leaves
    dropped). ``validation_errors`` maps user-input fields that failed leaf
    validation (range, type, ...); ``computed_errors`` maps formula keys that
    failed evaluation. They are kept separate because computed errors are
    *also* surfaced inline per-cell in the response shape, while validation
    errors are not (the cell is empty when validation fails).
    """

    values: dict[str, Any]
    validation_errors: dict[str, str] = field(default_factory=dict)
    computed_errors: dict[str, str] = field(default_factory=dict)

    @property
    def all_errors(self) -> dict[str, str]:
        """Both error maps merged (validation keys win on collision —
        a per-leaf failure is more directly actionable than a downstream
        formula failure that depends on the same cell)."""
        merged = dict(self.computed_errors)
        merged.update(self.validation_errors)
        return merged


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


class FillFormFromTextDTO(BaseModelDTO):
    """Request body for AI-assisted form filling from a text instruction.

    ``current_values`` is the form's current values dict — it is sent to the
    AI so it can keep / modify existing fields. The response is a
    ``FormSaveResultDTO``; nothing is persisted (the client reviews then calls
    ``POST /form/{id}/save``).
    """

    text: str
    current_values: dict[str, Any] = {}


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

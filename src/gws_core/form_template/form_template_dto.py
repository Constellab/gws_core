from datetime import datetime
from enum import Enum
from typing import Any

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.form.form_dto import FormSaveResultDTO
from gws_core.user.user_dto import UserDTO


class FormTemplateVersionStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class FormTemplateDTO(ModelWithUserDTO):
    name: str
    description: str | None
    is_archived: bool


class FormTemplateVersionDTO(ModelWithUserDTO):
    template_id: str
    version: int
    status: FormTemplateVersionStatus
    content: dict | None
    published_at: datetime | None
    published_by: UserDTO | None


class CreateFormTemplateDTO(BaseModelDTO):
    name: str
    description: str | None = None


class UpdateFormTemplateDTO(BaseModelDTO):
    name: str | None = None
    description: str | None = None


class CreateDraftVersionDTO(BaseModelDTO):
    copy_from_version_id: str | None = None


class TestFormTemplateVersionDTO(BaseModelDTO):
    """Request body for the "test a form" endpoint: validate a set of values
    against a form template version's specs without persisting anything.

    ``values`` are run through the version's ConfigSpecs exactly as a plain
    (non-submitting) save would: computed keys stripped, type validation,
    computed-value evaluation. The mandatory-field gate is not exercised
    (that only fires on a SUBMITTED transition, which has no meaning here).
    Works on DRAFT versions too — nothing is written.
    """

    values: dict[str, Any] = {}


class TestFormTemplateVersionResultDTO(BaseModelDTO):
    """Result of testing a set of values against a form template version.

    Mirrors what a SUBMITTED-transition save would surface, but without
    raising: the underlying ``FormSaveResultDTO`` (renderable values + specs,
    with computed cells already wrapped inline as ``{value, errors}``) plus
    a single flat ``errors`` list ready to display. The list is empty when
    the values would pass a real submit; otherwise it contains one
    human-readable string per failing check (missing mandatory, invalid
    leaf value, or computed-formula error).
    """

    result: FormSaveResultDTO
    errors: list[str]


class ReorderDraftFieldsDTO(BaseModelDTO):
    """Request body for reordering the fields of a DRAFT version.

    ``field_names`` is the full ordered list of field keys after the drag
    operation. The set of names must exactly match the version's current
    field set — no additions, no removals. Sending the complete order
    (rather than a from/to index) keeps the call idempotent and safe
    against concurrent edits.
    """

    field_names: list[str]


class ValidateComputedParamDTO(BaseModelDTO):
    """Request body for linting a candidate ComputedParam expression against a
    form template version's specs (the param itself need not exist yet).

    ``param_set_key`` targets the inner ConfigSpecs of that ParamSet — use it
    when the computed param will live inside a ParamSet (per-row formula). When
    None, the expression is validated against the version's outer specs.

    ``key`` is the intended key of the param being authored/edited. Supplying it
    makes the cycle check meaningful (e.g. editing ``density``'s expression to
    something that references ``density``, directly or transitively, is caught).
    When omitted, a synthetic key is used and only pre-existing cycles among the
    version's other computed params can surface.
    """

    expression: str
    param_set_key: str | None = None
    key: str | None = None


class ValidateComputedParamResultDTO(BaseModelDTO):
    """Result of validating a ComputedParam expression.

    ``valid`` is True only when the expression parses, every referenced key
    exists in the target scope, and adding the param introduces no cycle.
    ``referenced_keys`` lists the ConfigSpecs keys the expression depends on
    (always populated, even when invalid, as far as it could be parsed).
    ``error`` is None on success, a human-readable message otherwise.
    """

    valid: bool
    referenced_keys: list[str]
    error: str | None = None


class GenerateComputedParamDTO(BaseModelDTO):
    """Request body for AI-assisted ComputedParam expression generation.

    The AI is given the version's specs at the target scope (outer specs, or
    the inner specs of ``param_set_key`` when nesting) along with the user's
    free-text ``description``. It returns a single expression which is then
    run through the standard validator.
    """

    description: str
    param_set_key: str | None = None


class GenerateComputedParamResultDTO(BaseModelDTO):
    """Result of an AI-assisted ComputedParam expression generation.

    The expression is always returned — even when invalid — so the editor can
    display the suggestion alongside the validation error and let the user
    fix it.
    """

    expression: str
    validation: ValidateComputedParamResultDTO


class GenerateTemplateSpecsDTO(BaseModelDTO):
    """Request body for AI-assisted form-template field generation / editing.

    The AI is given the DRAFT version's current specs (which may be empty) and
    the user's free-text ``description``, and produces the complete new field
    specification. That spec is validated and **written onto the DRAFT** (the
    draft's whole field set is replaced); the updated version is returned. Empty
    current specs ⇒ build from scratch; non-empty ⇒ modify the existing fields.
    Only DRAFT versions can be targeted.
    """

    description: str


class GenerateTemplateFieldDTO(BaseModelDTO):
    """Request body for AI-assisted single-field generation / editing.

    The AI is given the DRAFT version's other fields (read-only context),
    ``field_key`` (the key of the field being edited, or null for a new field),
    ``current_field`` (the current spec of that field for an edit, or null for a
    new field — the AI starts from it and applies the description), and the
    user's free-text ``description``. It returns one proposed field. Nothing is
    persisted — the editor applies the result via the existing create/update
    field routes.
    """

    description: str
    field_key: str | None = None
    current_field: ParamSpecDTO | None = None


class GenerateTemplateFieldResultDTO(BaseModelDTO):
    """Result of an AI-assisted single-field generation.

    ``field_key`` is the proposed snake_case key (the AI may suggest one for a
    new field, or keep/rename the given one). ``spec`` is the field spec,
    serialized the same way as the field routes' bodies (``ParamSpecDTO``) so
    the editor can apply it directly. Nothing is persisted.
    """

    field_key: str
    spec: ParamSpecDTO

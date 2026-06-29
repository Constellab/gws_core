import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.logger import Logger

from ...core.classes.validator import DictValidator, ListValidator
from .param_spec import FloatParam, ParamSpec
from .param_types import ParamSpecDTO, ParamSpecType, ParamSpecVisibilty


class ParamSetDefaultRowsMode(Enum):
    """How the ``default_rows`` of a :class:`ParamSet` behave for the user.

    More modes can be added over time (e.g. lock whole rows, lock-all-cells).
    """

    # Presets are only a pre-fill: every cell stays editable, no row is pinned.
    EDITABLE = "editable"

    # Each non-None cell explicitly provided in a preset is locked (not editable)
    # on the incoming row at the same position; cells left out or set to None stay
    # editable for the user to fill.
    LOCK_PROVIDED = "lock_provided"


@dataclass
class ParamSetRowsValidationResult:
    """Outcome of :meth:`ParamSet.validate_lenient`.

    ``errors`` keys are ``"[<row_index>].<inner_key>"`` — the caller in
    :meth:`ConfigSpecs.validate_values` prepends the ParamSet key to form
    the final ``"<paramset>[<row>].<inner>"`` shape.
    """

    rows: list[dict[str, Any]]
    errors: dict[str, str] = field(default_factory=dict)


@param_spec_decorator(category=ParamSpecCategory.PARAM_SET)
class ParamSet(ParamSpec):
    """ParamSet. Use to define a group of parameters that can be added multiple times. This will
    provid a list of dictionary as values : List[Dict[str, Any]]

    """

    param_set: ConfigSpecs
    max_number_of_occurrences: int | None
    min_number_of_occurrences: int | None
    # Preset rows used as the initial value. Each row is a full dict (inner spec
    # defaults merged with the provided values) carrying its own reserved
    # ``ConfigSpecs.ITEM_ID_KEY``. ``None`` means "no presets".
    default_rows: list[dict[str, Any]] | None
    # How the preset rows behave for the user (editable pre-fill vs. locked
    # cells). Enforced server-side in ``_validate_rows``.
    default_rows_mode: ParamSetDefaultRowsMode

    def __init__(
        self,
        param_set: ConfigSpecs | None = None,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
        max_number_of_occurrences: int | None = None,
        min_number_of_occurrences: int | None = 1,
        default_rows: list[dict[str, Any]] | None = None,
        default_rows_mode: ParamSetDefaultRowsMode = ParamSetDefaultRowsMode.EDITABLE,
    ):
        """
        :param visibility: Visibility of the param. It override all child spec visibility. see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param max_number_of_occurrences: Nb max of occurence of values the params. If negative or None, there is no limit.
        :type max_number_of_occurrences: Optional[str]
        :param min_number_of_occurrences: Nb min of rows. Defaults to 1. Set to 0 to make the ParamSet optional
            (it may then have 0 rows, the value being an empty array []). Negative or None is treated as 0.
        :type min_number_of_occurrences: Optional[int]
        :param default_rows: Preset rows used as the initial value. Each row is a partial dict keyed by inner-spec
            key; unspecified inner fields fall back to their own default. Rows may carry a ``__item_id`` to keep a
            stable identity; otherwise a deterministic one is generated.
        :type default_rows: Optional[list[dict]]
        :param default_rows_mode: How the ``default_rows`` behave for the user. ``EDITABLE`` (default) makes them a
            plain pre-fill. ``LOCK_PROVIDED`` pins each non-None cell provided in a preset (the user cannot edit it
            nor remove the row); cells left out or set to None stay editable. Any mode other than ``EDITABLE``
            requires ``default_rows``. Enforced server-side.
        :type default_rows_mode: ParamSetDefaultRowsMode
        """

        self.max_number_of_occurrences = max_number_of_occurrences
        self.min_number_of_occurrences = min_number_of_occurrences
        self._check_occurrence_bounds()

        if param_set is None:
            param_set = ConfigSpecs()

        if isinstance(param_set, dict):
            Logger.warning("ParamSet: param_set should be a ConfigSpecs object, not a dict. ")
            param_set = ConfigSpecs(param_set)

        self.param_set = param_set
        self.default_rows_mode = default_rows_mode
        self.default_rows = self._build_default_rows(default_rows)

        # optional is derived: a ParamSet is optional iff it allows 0 rows.
        optional = self._is_optional_for(min_number_of_occurrences)
        super().__init__(
            default_value=[] if optional else None,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @staticmethod
    def _is_optional_for(min_number_of_occurrences: int | None) -> bool:
        """A ParamSet is optional iff it accepts 0 rows (min is 0 / None / negative)."""
        return min_number_of_occurrences is None or min_number_of_occurrences <= 0

    def _check_occurrence_bounds(self) -> None:
        """Reject a spec whose max occurrence is below its min.

        Only checked when both bounds are concrete limits: a negative or ``None``
        max means "no upper limit", and a negative or ``None`` min is treated as
        0 — neither can be inconsistent. Effective min is ``max(min, 0)``.
        """
        max_occ = self.max_number_of_occurrences
        min_occ = self.min_number_of_occurrences
        if max_occ is None or max_occ < 0:
            return
        effective_min = max(min_occ, 0) if min_occ is not None else 0
        if max_occ < effective_min:
            raise BadRequestException(
                f"ParamSet: max_number_of_occurrences ({max_occ}) cannot be lower than "
                f"min_number_of_occurrences ({effective_min})."
            )

    def clone_with_inner_specs(self, inner_specs: ConfigSpecs) -> "ParamSet":
        """Return a copy of this ParamSet with its inner specs replaced.

        Every other attribute (occurrence bounds, presets, mode, visibility,
        ...) is carried over verbatim, so callers that need a structurally
        identical ParamSet over different inner specs — e.g. building a probe
        ConfigSpecs for cycle detection — don't have to enumerate the fields
        (and silently drift when a new one is added).

        ``default_rows`` are copied as-is (already-built provided cells), not
        re-validated against ``inner_specs``.
        """
        clone = ParamSet(
            param_set=inner_specs,
            visibility=self.visibility,
            human_name=self.human_name,
            short_description=self.short_description,
            max_number_of_occurrences=self.max_number_of_occurrences,
            min_number_of_occurrences=self.min_number_of_occurrences,
        )
        # Set mode + presets after construction so the "mode requires
        # default_rows" guard isn't tripped, and the already-built presets are
        # carried over verbatim (not re-validated against the new inner specs).
        clone.default_rows_mode = self.default_rows_mode
        clone.default_rows = (
            None if self.default_rows is None else [dict(row) for row in self.default_rows]
        )
        return clone

    def _build_default_rows(
        self, default_rows: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """Normalize raw preset rows into lists of provided cells.

        Presets are POSITIONAL: each stored row holds ONLY the explicitly-
        provided cells (no ``__item_id`` — ids are minted on validation exactly
        like rows that have no default at all). Inner spec defaults are merged in
        lazily by ``get_default_value``. The lock pins these provided cells onto
        the incoming row at the same index.
        """
        if default_rows is None:
            if self.default_rows_mode != ParamSetDefaultRowsMode.EDITABLE:
                raise BadRequestException(
                    f"ParamSet: default_rows_mode={self.default_rows_mode.value} requires "
                    "default_rows to be set."
                )
            return None

        built: list[dict[str, Any]] = []
        for index, row in enumerate(default_rows):
            provided = {k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY}

            # Validate the preset against the inner ConfigSpecs so a malformed
            # row fails loud at spec-definition time, not silently on every save.
            # Unknown keys / bad leaf values always raise. Mandatories are NOT
            # required even when locked: the lock pins only the provided cells —
            # the user still fills the empty (not-provided) ones.
            self._check_default_row(provided, index)

            built.append(provided)

        if (
            self.max_number_of_occurrences is not None
            and self.max_number_of_occurrences >= 0
            and len(built) > self.max_number_of_occurrences
        ):
            raise BadRequestException(
                f"ParamSet: {len(built)} default_rows exceed max_number_of_occurrences "
                f"{self.max_number_of_occurrences}."
            )

        return built

    def _check_default_row(self, provided: dict[str, Any], index: int) -> None:
        """Validate one preset row against the inner ConfigSpecs at spec-definition time.

        - Unknown keys raise (catches developer typos like ``naem``).
        - Each provided leaf value is validated through its ``ParamSpec.validate``.

        Mandatories are intentionally NOT required, even for locked presets: a
        lock pins only the provided cells; the user fills the rest.
        """
        specs = self.param_set.specs

        unknown_keys = set(provided) - set(specs)
        if unknown_keys:
            raise BadRequestException(
                f"ParamSet default_rows[{index}]: unknown field(s) "
                f"{sorted(unknown_keys)}. Valid fields: {sorted(specs)}."
            )

        for key, value in provided.items():
            spec = specs[key]
            if value is None or not spec.accepts_user_input:
                continue
            try:
                spec.validate(value)
            except BadRequestException as err:
                raise BadRequestException(f"ParamSet default_rows[{index}].{key}: {err}") from err

    @property
    def _locked_default_cells(self) -> list[dict[str, Any]]:
        """Locked preset cells, POSITIONAL (aligned with the default rows order).

        Each entry holds only the cells the user may NOT edit on the incoming
        row at the same index: the explicitly-provided cells with a non-None
        value (no inner-default fill, no id). A None-valued preset cell is an
        empty cell — it pins nothing, so the user's value wins. Empty list when
        there are no presets or the mode is not ``LOCK_PROVIDED``.
        """
        if (
            self.default_rows_mode != ParamSetDefaultRowsMode.LOCK_PROVIDED
            or self.default_rows is None
        ):
            return []
        return [
            {k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY and v is not None}
            for row in self.default_rows
        ]

    def get_default_value(self) -> list:
        if self.default_rows is not None:
            # merge inner-spec defaults under each preset's provided cells so
            # unspecified fields still get their per-spec default. No __item_id:
            # presets are positional and ids are minted on validation, exactly
            # like rows that have no default at all.
            base_defaults = self.param_set.get_default_values()
            return [
                {
                    **base_defaults,
                    **{k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY},
                }
                for row in self.default_rows
            ]

        if self.optional:
            return []

        # if this is not optional, return an array of 1 element with the
        # default value of each param_spec
        return [self.param_set.get_default_values()]

    def validate(self, value: list[dict[str, Any]]) -> Any:
        """Validate a ParamSet value (list of row dicts) and reconcile per-row
        identity.

        Each row carries a reserved ``ConfigSpecs.ITEM_ID_KEY`` (``__item_id``)
        — a UUID v4 stable across saves. Clients should generate it themselves
        for new rows; the server fills it in if missing. Duplicate ids within
        the same ParamSet are rejected.

        The id is stripped before delegating to the inner
        ``ConfigSpecs.get_and_check_values`` (which would otherwise reject the
        unknown reserved key) and re-attached on the validated dict.
        """
        return self._validate_rows(value, lenient=False).rows

    def validate_lenient(self, value: list[dict[str, Any]]) -> ParamSetRowsValidationResult:
        """Lenient variant of ``validate`` — runs leaf-level validation on
        provided values but does NOT raise on missing inner mandatories or
        on per-leaf validation failures.

        Errors are returned alongside the validated rows; each key is
        ``"[<row_index>].<inner_key>"`` (no leading ParamSet key — the
        caller prepends it). Used by the form-save flow, where errors are
        rendered per-field and missing mandatories only block on the
        SUBMITTED transition.
        """
        return self._validate_rows(value, lenient=True)

    def _validate_rows(
        self, value: list[dict[str, Any]], lenient: bool, enforce_occurrences: bool = True
    ) -> ParamSetRowsValidationResult:
        if value is None:
            return ParamSetRowsValidationResult(rows=[])
        # ``enforce_occurrences`` is False when validating the default value: the
        # default may legitimately hold fewer rows than min_number_of_occurrences
        # (e.g. an empty list, or fewer preset rows than the min the user must end
        # up with), so the row-count bounds must not be checked there.
        list_validator = ListValidator(
            min_number_of_occurrences=self.min_number_of_occurrences
            if enforce_occurrences
            else None,
            max_number_of_occurrences=self.max_number_of_occurrences
            if enforce_occurrences
            else None,
        )
        dict_validator = DictValidator()

        # Locked preset cells, POSITIONAL: the cells at index i are pinned onto
        # the incoming row at index i. Presets carry no id, so the lock is
        # matched by row position, not identity.
        locked_default_cells = self._locked_default_cells

        # global validation of the list
        list_: list[dict[str, Any]] = list_validator.validate(value)

        result_list = []
        errors: dict[str, str] = {}
        seen_ids: set[str] = set()
        for row_index, dict_ in enumerate(list_):
            # Valid on dict of param set
            valid_dict = dict_validator.validate(dict_)

            item_id = valid_dict.get(ConfigSpecs.ITEM_ID_KEY) or str(uuid.uuid4())
            if item_id in seen_ids:
                raise BadRequestException(
                    f"Duplicate {ConfigSpecs.ITEM_ID_KEY} '{item_id}' in ParamSet"
                )
            seen_ids.add(item_id)

            # Pin the locked cells for this position BEFORE validation, so the
            # locked value (not the client's edit) is what gets validated and a
            # locked cell is never reported as missing.
            if row_index < len(locked_default_cells):
                valid_dict = {**valid_dict, **locked_default_cells[row_index]}

            if lenient:
                row_result = self.param_set.validate_values(valid_dict)
                validated_item = row_result.values
                for inner_key, message in row_result.errors.items():
                    errors[f"[{row_index}].{inner_key}"] = message
            else:
                # get_and_check_values iterates self.specs only, so __item_id is
                # silently ignored by it; no need to strip the input.
                validated_item = self.param_set.get_and_check_values(valid_dict)

            validated_item[ConfigSpecs.ITEM_ID_KEY] = item_id
            result_list.append(validated_item)

        return ParamSetRowsValidationResult(rows=result_list, errors=errors)

    @staticmethod
    def diff_values(
        key: str,
        old_val: Any,
        new_val: Any,
    ) -> list:
        """Diff two ParamSet values (lists of row dicts) by ``__item_id``.

        Produces:
        - PARAMSET_ITEM_REMOVED for ids only in old (path: ``key[item_id=<uuid>]``).
        - PARAMSET_ITEM_ADDED for ids only in new.
        - One FIELD_CREATED / FIELD_UPDATED / FIELD_DELETED per inner field change
          for ids present on both sides (path: ``key[item_id=<uuid>].<field>``).

        Reorder = same set of ids on both sides with no inner change → no entries.

        ``__item_id`` is stripped from old_value / new_value payloads on
        ITEM_ADDED / ITEM_REMOVED entries — the path already carries the id.
        """
        old_rows: list[dict[str, Any]] = old_val if isinstance(old_val, list) else []
        new_rows: list[dict[str, Any]] = new_val if isinstance(new_val, list) else []

        old_by_id: dict[str, dict[str, Any]] = {
            row[ConfigSpecs.ITEM_ID_KEY]: row
            for row in old_rows
            if isinstance(row, dict) and row.get(ConfigSpecs.ITEM_ID_KEY)
        }
        new_by_id: dict[str, dict[str, Any]] = {
            row[ConfigSpecs.ITEM_ID_KEY]: row
            for row in new_rows
            if isinstance(row, dict) and row.get(ConfigSpecs.ITEM_ID_KEY)
        }

        changes: list = []

        for item_id in sorted(set(old_by_id) - set(new_by_id)):
            changes.append(
                ConfigChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=ConfigChangeAction.PARAMSET_ITEM_REMOVED,
                    old_value=ParamSet._strip_id(old_by_id[item_id]),
                    new_value=None,
                )
            )
        for item_id in sorted(set(new_by_id) - set(old_by_id)):
            changes.append(
                ConfigChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=ConfigChangeAction.PARAMSET_ITEM_ADDED,
                    old_value=None,
                    new_value=ParamSet._strip_id(new_by_id[item_id]),
                )
            )

        for item_id in sorted(set(old_by_id) & set(new_by_id)):
            old_row = old_by_id[item_id]
            new_row = new_by_id[item_id]
            inner_keys = (set(old_row.keys()) | set(new_row.keys())) - {ConfigSpecs.ITEM_ID_KEY}
            for inner_key in sorted(inner_keys):
                in_old = inner_key in old_row
                in_new = inner_key in new_row
                old_inner = old_row.get(inner_key)
                new_inner = new_row.get(inner_key)
                inner_path = f"{key}[item_id={item_id}].{inner_key}"
                changes.extend(
                    ConfigSpecs.diff_scalar(inner_path, old_inner, new_inner, in_old, in_new)
                )

        return changes

    @staticmethod
    def _strip_id(row: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY}

    def to_dto(self) -> ParamSpecDTO:
        json_: ParamSpecDTO = super().to_dto()

        # convert the additional info to json
        json_.additional_info = {
            "max_number_of_occurrences": self.max_number_of_occurrences,
            "min_number_of_occurrences": self.min_number_of_occurrences,
            "default_rows": self.default_rows,
            "default_rows_mode": self.default_rows_mode.value,
            "param_set": self.param_set.to_dto(),
        }

        return json_

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.PARAM_SET

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return (
            "A repeatable group of rows — each row is a small set of fields the "
            "user can add several times (e.g. a list of samples)."
        )

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        return {
            "param_set": "Object mapping each ROW field KEY to its spec (same shape as a top-level field).",
            "max_number_of_occurrences": "Maximum number of rows, or -1 / null for no limit.",
            "min_number_of_occurrences": "Minimum number of rows, or -1 / null for no minimum.",
            "default_rows": "Preset rows used as the initial value. List of row dicts (field KEY -> value); "
            "unspecified fields fall back to their default.",
            "default_rows_mode": "How default_rows behave: 'editable' (plain pre-fill) or 'lock_provided' "
            "(each non-null provided cell is locked and the row not removable; other cells stay editable).",
        }

    @classmethod
    def ai_example_spec(cls) -> "ParamSet":
        # Built from real inner params so the serialized example shows the exact
        # nested shape (additional_info.param_set) the deserializer expects.
        return cls(
            ConfigSpecs(
                {
                    "mass": FloatParam(human_name="Mass", short_description="Mass in grams"),
                    "volume": FloatParam(human_name="Volume", optional=True),
                }
            ),
            human_name="Samples",
        )

    @staticmethod
    def _load_default_rows_mode(additional_info: dict) -> ParamSetDefaultRowsMode:
        """Resolve the default-rows mode from a serialized spec.

        Reads the ``default_rows_mode`` enum value, falling back to the legacy
        boolean ``lock_default_rows`` for specs serialized before the enum.
        """
        raw_mode = additional_info.get("default_rows_mode")
        if raw_mode is not None:
            return ParamSetDefaultRowsMode(raw_mode)
        # legacy boolean fallback
        if additional_info.get("lock_default_rows"):
            return ParamSetDefaultRowsMode.LOCK_PROVIDED
        return ParamSetDefaultRowsMode.EDITABLE

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> "ParamSet":
        from .param_spec_helper import ParamSpecHelper

        # Defer default-value validation: the base class would validate it before
        # the bounds/specs below are set (i.e. against a half-built ParamSet), and
        # it would enforce the occurrence count, which must NOT apply to the
        # default value. We re-run it ourselves at the end, occurrence-free.
        param_set: ParamSet = super().load_from_dto(spec_dto, validate=False)

        # load info from additional info
        param_set.max_number_of_occurrences = spec_dto.additional_info.get(
            "max_number_of_occurrences"
        )
        if "min_number_of_occurrences" in spec_dto.additional_info:
            param_set.min_number_of_occurrences = spec_dto.additional_info[
                "min_number_of_occurrences"
            ]
            # keep optional coherent with the (authoritative) min on new specs
            param_set.optional = cls._is_optional_for(param_set.min_number_of_occurrences)
        else:
            # legacy spec without min: derive min from the serialized optional flag
            param_set.min_number_of_occurrences = 0 if param_set.optional else 1
        if validate:
            param_set._check_occurrence_bounds()
        param_set.default_rows_mode = cls._load_default_rows_mode(spec_dto.additional_info)
        # default_rows store only the provided cells, positionally (no __item_id).
        # Strip any stray id a legacy/serialized payload may carry. No re-validation.
        raw_default_rows = spec_dto.additional_info.get("default_rows")
        if raw_default_rows is None:
            param_set.default_rows = None
        else:
            param_set.default_rows = [
                {k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY}
                for row in raw_default_rows
            ]

        specs = ConfigSpecs()

        param_set_info: dict = spec_dto.additional_info.get("param_set") or {}
        for key, param in param_set_info.items():
            specs.add_spec(
                key, ParamSpecHelper.create_param_spec_from_json(param, validate=validate)
            )

        param_set.param_set = specs

        if validate and param_set.default_value is not None:
            # The default value is checked LENIENTLY: only the compatibility of
            # the values that ARE provided is verified. Missing mandatory inner
            # fields and None cells are tolerated (a default row may legitimately
            # leave the user to fill the mandatory cells), and the occurrence
            # bounds are not enforced. Only a genuinely incompatible value (wrong
            # type / out-of-range) makes the spec invalid.
            try:
                result = param_set._validate_rows(
                    param_set.default_value, lenient=True, enforce_occurrences=False
                )
            except Exception as err:
                raise BadRequestException(
                    f"Invalid default value for field '{param_set.human_name}': {err}"
                ) from err
            if result.errors:
                raise BadRequestException(
                    f"Invalid default value for field '{param_set.human_name}': "
                    f"{'; '.join(f'{k}: {v}' for k, v in result.errors.items())}"
                )

        return param_set

import copy
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.config_exceptions import MissingConfigsException, UnkownParamException
from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

from .param.param_spec import ParamSpec
from .param.param_types import ParamSpecDTO


@dataclass
class ValidateValuesResult:
    """Outcome of :meth:`ConfigSpecs.validate_values`.

    ``values`` is the reshaped value dict with invalid leaves dropped (so
    downstream consumers never see bad data). ``errors`` keys mirror the
    computed-error keying convention with row indices for ParamSet rows:
    ``"<key>"`` outer-scope, ``"<paramset>[<row>].<inner>"`` inside a row.
    """

    values: ConfigParamsDict
    errors: dict[str, str] = field(default_factory=dict)


class ConfigSpecs:
    """A typed schema (dict of ParamSpec) plus value-management helpers.

    The helpers (strip_computed_keys, validate_values, merge_computed,
    diff_values) operate on a values dict shaped by these specs.

    ITEM_ID_KEY is the reserved per-row key on ParamSet items. ParamSet.validate
    mints, preserves, and restores it; nothing else in ConfigSpecs writes it.
    """

    ITEM_ID_KEY: ClassVar[str] = "__item_id"

    # Max length of a spec key. Applies to every ConfigSpecs (tasks, views,
    # forms, ...). Enforced by _spec_key_error on construction and by the
    # imperative mutators (add_spec / add_or_update_spec). Set well above the
    # longest existing keys in the codebase so it only rejects absurd ones.
    MAX_KEY_LENGTH: ClassVar[int] = 40

    # Field-key shapes accepted by ``format_field_key``:
    #   ``"<key>"``                       outer-scope leaf or computed
    #   ``"<paramset>[].<inner>"``        ParamSet inner computed (formula
    #                                     applies uniformly across rows, so
    #                                     no row index)
    #   ``"<paramset>[<row>].<inner>"``   ParamSet inner leaf (row-specific,
    #                                     e.g. range failure on a single row)
    # The middle group captures the row index (or empty for the [] case).
    _FIELD_KEY_RE: ClassVar[re.Pattern] = re.compile(r"^([^\[]+)\[(\d*)\]\.(.+)$")

    specs: dict[str, ParamSpec]

    # Validity state recorded at construction. __init__ never raises on an
    # invalid param key (a ConfigSpecs is built during class-body evaluation,
    # before the task/view decorator runs — raising there would abort the
    # whole module import). Instead the decorator checks is_valid and skips
    # registering the task/view. Runtime callers that want loud failure call
    # assert_valid().
    is_valid: bool
    invalid_reason: str | None

    def __init__(
        self,
        specs: dict[str, ParamSpec] | None = None,
        _skip_key_validation: bool = False,
    ) -> None:
        """Define the spec of a task or a view
        Example:
        ConfigSpecs({
            "param1": IntParam(human_name="Param 1", default_value=1),
            "param2": StrParam(human_name="Param 2", default_value="Hello")
        })

        :param specs: _description_, defaults to None
        :type specs: Dict[str, ParamSpec], optional
        :param _skip_key_validation: internal flag used by from_json/from_dto
            to rehydrate persisted specs without re-validating their keys.
            Do not set from user code.
        """
        if specs is None:
            specs = {}

        self.is_valid = True
        self.invalid_reason = None

        for key, spec in specs.items():
            # invalid param key (skipped when rehydrating persisted specs)
            if not _skip_key_validation:
                error = self._spec_key_error(key)
                if error is not None:
                    # Record the problem instead of raising: the task/view
                    # decorator will see is_valid=False and mark the typing as
                    # errored. specs is left empty so no consumer reads a
                    # malformed key.
                    self.is_valid = False
                    self.invalid_reason = error
                    self.specs = {}
                    return

            # a ParamSpec that failed to build (e.g. an invalid default value)
            # propagates its invalidity to the whole ConfigSpecs
            if isinstance(spec, ParamSpec) and not spec.is_valid:
                self.is_valid = False
                self.invalid_reason = f"Invalid spec '{key}': {spec.invalid_reason}"
                self.specs = {}
                return

        self.specs = specs

    @classmethod
    def _spec_key_error(cls, key: str) -> str | None:
        """Return an error message if the key is invalid, None otherwise.

        A valid key contains only letters, digits, and underscores, does not
        start with a digit, and is at most ``MAX_KEY_LENGTH`` characters. Keeps
        spec keys readable as variable-like tokens.
        """
        if not isinstance(key, str) or not key.isidentifier():
            return (
                f"Invalid param key '{key}': must contain only letters, digits, "
                f"and underscores, and cannot start with a digit."
            )
        if len(key) > cls.MAX_KEY_LENGTH:
            return f"Invalid param key '{key}': too long (max {cls.MAX_KEY_LENGTH} characters)."
        return None

    @classmethod
    def _assert_spec_key(cls, key: str) -> None:
        """Raising variant of :meth:`_spec_key_error`, used by the imperative
        mutators (add_spec, add_or_update_spec) which run at runtime and should
        fail loudly on a bad key.
        """
        error = cls._spec_key_error(key)
        if error is not None:
            raise BadRequestException(error)

    def assert_valid(self) -> None:
        """Raise if this ConfigSpecs was built with an invalid definition.

        Explicit fail-fast hook for runtime/non-class-body callers. The
        constructor itself never raises (see is_valid).
        """
        if not self.is_valid:
            raise Exception(self.invalid_reason)

    def has_spec(self, spec_name: str) -> bool:
        return spec_name in self.specs

    def has_specs(self) -> bool:
        return len(self.specs) > 0

    def check_spec_exists(self, spec_name: str) -> None:
        if not self.has_spec(spec_name):
            raise UnkownParamException(spec_name)

    def get_spec(self, spec_name: str) -> ParamSpec:
        self.check_spec_exists(spec_name)
        return self.specs[spec_name]

    def update_spec(self, spec_name: str, spec: ParamSpec) -> None:
        self.check_spec_exists(spec_name)
        self.specs[spec_name] = spec

    def add_spec(self, spec_name: str, spec: ParamSpec) -> None:
        self._assert_spec_key(spec_name)
        if spec_name in self.specs:
            raise Exception(f"The spec '{spec_name}' already exists")
        self.specs[spec_name] = spec

    def add_or_update_spec(self, spec_name: str, spec: ParamSpec) -> None:
        self._assert_spec_key(spec_name)
        self.specs[spec_name] = spec

    def remove_spec(self, spec_name: str) -> None:
        self.check_spec_exists(spec_name)
        del self.specs[spec_name]

    def get_specs_as_dict(self) -> dict[str, ParamSpec]:
        """Return a copy of the specs dictionary.

        Useful for unpacking specs into a new ConfigSpecs, e.g.:
            ConfigSpecs({
                "my_param": StrParam(...),
                **other_config_specs.get_specs_as_dict(),
            })
        """
        return dict(self.specs)

    def merge_specs(self, specs2: "ConfigSpecs") -> "ConfigSpecs":
        """Merge two ConfigSpecs objects"""
        for key, spec in specs2.specs.items():
            self.add_or_update_spec(key, spec)
        return self

    def to_dto(self, skip_private: bool = True) -> dict[str, ParamSpecDTO]:
        """convert the config specs to json"""
        json_: dict[str, Any] = {}
        for key, spec in self.specs.items():
            # skip private params
            if skip_private and spec.visibility == "private":
                continue
            json_[key] = spec.to_dto()

        return json_

    def to_json_dict(self, skip_private: bool = True) -> dict[str, Any]:
        """convert the config specs to json"""
        dto = self.to_dto(skip_private)
        return {key: value.to_json_dict() for key, value in dto.items()}

    def all_config_are_optional(self) -> bool:
        """Check if all the config are optional"""
        return all(spec.optional for spec in self.specs.values())

    def has_visible_config_specs(self) -> bool:
        """Check if the config has visible specs"""
        return any(spec.visibility != "private" for spec in self.specs.values())

    def mandatory_values_are_set(self, param_values: ConfigParamsDict) -> bool:
        """
        check that all mandatory configs are provided
        """
        return not self.get_missing_mandatory_paths(param_values)

    def get_missing_mandatory_paths(self, param_values: ConfigParamsDict) -> list[str]:
        """Return paths of every missing mandatory field, recursing into ParamSet rows.

        Path format uses human_name (with spec key as fallback):
        - top-level scalar:   ``Mass``
        - ParamSet row field: ``Samples[0].Mass`` (0-based row index)

        Empty list means all mandatories are set. Used by the form save flow
        to surface a precise list of what is missing on the SUBMITTED gate.
        """
        from .param.param_set import ParamSet

        if not self.specs:
            return []

        missing: list[str] = []
        for key, spec in self.specs.items():
            # System-derived params (e.g. ComputedParam) are never required from the user.
            if not spec.accepts_user_input:
                continue
            value = (param_values or {}).get(key)
            display_name = spec.human_name or key
            if isinstance(spec, ParamSet) and spec.param_set is not None:
                if not spec.optional and not value:
                    missing.append(display_name)
                    continue
                if not isinstance(value, list):
                    continue
                for row_index, row in enumerate(value):
                    if not isinstance(row, dict):
                        continue
                    for inner_missing in spec.param_set.get_missing_mandatory_paths(row):
                        missing.append(f"{display_name}[{row_index}].{inner_missing}")
                continue
            if not spec.optional and value is None:
                missing.append(display_name)

        return missing

    def check_config_specs(self) -> None:
        """Check that the config specs are valid.

        Validates spec keys (shape + length) and types, and delegates to
        ComputedParamGraphChecker for cycle detection and reference validation
        across computed expressions (which already recurses into ParamSets).
        Key validation also recurses into ParamSet inner specs.
        """
        if not self.specs:
            return

        if not isinstance(self.specs, dict):
            raise Exception("The config specs must be a dictionary")

        for key, item in self.specs.items():
            if not isinstance(item, ParamSpec):
                raise Exception(
                    f"The config spec '{key}' is invalid, it must be a ParamSpec but got {type(item)}"
                )
        self._check_keys_recursive()

        from gws_core.config.param.computed.computed_param_graph import (
            ComputedParamGraphChecker,
        )

        ComputedParamGraphChecker.check(self)

    def _check_keys_recursive(self) -> None:
        """Validate every spec key (shape + length), recursing into ParamSet
        inner specs. Raises on the first invalid key."""
        from .param.param_set import ParamSet

        for key, item in self.specs.items():
            key_error = self._spec_key_error(key)
            if key_error is not None:
                raise BadRequestException(key_error)
            if isinstance(item, ParamSet) and item.param_set is not None:
                item.param_set._check_keys_recursive()

    def build_config_params(self, param_values: ConfigParamsDict) -> ConfigParams:
        """
        Build the ConfigParams from the param_specs and param_values.
        ConfigParam is supposed to be used directly not stored.
        Check the param_values with params_specs and return ConfigParams if ok.
        ConfigParams contains all value and default value if not provided.

        Computed params (accepts_user_input=False) are evaluated after
        validation and merged into the returned ConfigParams.

        :param param_specs: [description]
        :type param_specs: ConfigSpecs
        :param param_values: [description]
        :type param_values: ConfigParamsDict
        :return: [description]
        :rtype: ConfigParams
        """
        values = self.get_and_check_values(param_values)

        # apply transform function of specs if needed
        for key, spec in self.specs.items():
            values[key] = spec.build(values[key])

        # compute_values is best-effort: errors on individual fields surface as
        # None values with a per-field error in the result dict, so they don't
        # break task/view runs. Form save will read and surface the errors.
        computed, _errors = self.compute_values(values)
        values.update(computed)

        return ConfigParams(values)

    def get_and_check_values(self, param_values: ConfigParamsDict) -> ConfigParamsDict:
        """
        Check and validate all values based on spec
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        if param_values is None:
            param_values = {}

        full_values: ConfigParamsDict = {}
        missing_params: list[str] = []

        for key, spec in self.specs.items():
            # System-derived params (e.g. ComputedParam) are never validated
            # from user input. They get None on the input pass; their real
            # value comes from compute_values(...).
            if not spec.accepts_user_input:
                full_values[key] = None
                continue

            # if the config was not set
            if key not in param_values or param_values[key] is None:
                if spec.optional:
                    full_values[key] = spec.get_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(spec.human_name or key)
            else:
                full_values[key] = spec.validate(param_values[key])

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return full_values

    def get_default_values(self) -> ConfigParamsDict:
        default_values = {}
        for key, spec in self.specs.items():
            # Computed entries don't have a "default" — they're evaluated.
            if not spec.accepts_user_input:
                default_values[key] = None
                continue
            default_values[key] = spec.get_default_value()
        return default_values

    def compute_values(
        self,
        values: ConfigParamsDict,
        evaluator: Any = None,
    ) -> tuple[ConfigParamsDict, dict[str, str]]:
        """Evaluate all entries with accepts_user_input=False over the provided
        values and return (computed_values, errors_by_key).

        Thin delegator to ComputedParamResolver.compute_all — see that method
        for the full contract.
        """
        from gws_core.config.param.computed.computed_param_resolver import (
            ComputedParamResolver,
        )

        return ComputedParamResolver.compute_all(self, values, evaluator)

    # ------------------------------------------------------------------ #
    # Values-layer helpers
    # ------------------------------------------------------------------ #

    def strip_computed_keys(self, values: ConfigParamsDict) -> ConfigParamsDict:
        """Drop keys whose ``spec.accepts_user_input is False`` (currently
        ``ComputedParam``). Recurses into ParamSet rows.

        Defensive input-side strip: clients must not write to computed keys;
        the evaluator owns those values.
        """
        # ParamSet imported lazily: param_set.py imports ConfigSpecs at its
        # module top, so a top-level import here would form a cycle.
        from .param.param_set import ParamSet

        if not values:
            return {} if values is None else values
        result: ConfigParamsDict = {}
        for key, value in values.items():
            spec = self.specs.get(key)
            if spec is not None and not spec.accepts_user_input:
                continue
            if (
                isinstance(spec, ParamSet)
                and spec.param_set is not None
                and isinstance(value, list)
            ):
                # Recurse into each row using the inner ConfigSpecs. __item_id
                # is not a spec so it falls into the unknown-key branch and is
                # preserved naturally.
                result[key] = [
                    spec.param_set.strip_computed_keys(row)
                    for row in value
                    if isinstance(row, dict)
                ]
            else:
                result[key] = value
        return result

    def validate_values(self, values: ConfigParamsDict) -> ValidateValuesResult:
        """Run leaf-level ``ParamSpec.validate(...)`` on every provided value.

        Lenient on two axes:
        - missing mandatories DO NOT raise (use ``mandatory_values_are_set``
          as a separate gate when required);
        - per-leaf ``ParamSpec.validate`` failures are *collected* into the
          returned ``errors`` dict instead of aborting the whole pass. The
          offending value is dropped from the result so downstream consumers
          (computed evaluation, persistence) don't see invalid data.

        Error keys mirror computed errors:
        - ``"<key>"`` for outer-scope leaves;
        - ``"<paramset>[<row_index>].<inner>"`` for ParamSet rows (row index
          included because a range failure is per-row data, unlike computed
          errors which apply uniformly across rows).

        For ParamSets, ``ParamSet.validate_lenient`` mints ``__item_id`` per
        row and the result carries it back. Callers that want the old
        raise-on-error contract should use :meth:`validate_values_or_raise`.
        """
        if not values:
            return ValidateValuesResult(values={} if values is None else values)

        from .param.param_set import ParamSet

        result: ConfigParamsDict = {}
        errors: dict[str, str] = {}
        for key, value in values.items():
            spec = self.specs.get(key)
            if spec is None or not spec.accepts_user_input:
                result[key] = value
                continue
            if value is None:
                result[key] = None
                continue
            if isinstance(spec, ParamSet):
                row_result = spec.validate_lenient(value)
                result[key] = row_result.rows
                for inner_key, message in row_result.errors.items():
                    errors[f"{key}{inner_key}"] = message
            else:
                try:
                    result[key] = spec.validate(value)
                except BadRequestException as err:
                    errors[key] = str(err)
        return ValidateValuesResult(values=result, errors=errors)

    def validate_values_or_raise(self, values: ConfigParamsDict) -> ConfigParamsDict:
        """Raise-on-error wrapper around :meth:`validate_values`.

        Aggregates every leaf-validation failure into a single
        ``BadRequestException`` (rather than the old fail-fast behavior where
        the first invalid field aborted). Use from non-form callers that want
        the legacy raising contract; the form pipeline uses ``validate_values``
        directly so it can render per-field diagnostics.
        """
        result = self.validate_values(values)
        if result.errors:
            raise BadRequestException(
                "Invalid values: " + "; ".join(f"{k}: {msg}" for k, msg in result.errors.items())
            )
        return result.values

    def format_field_key(self, field_key: str) -> str:
        """Translate an internal field-key into a human-readable label using
        ``spec.human_name`` (falling back to the raw key when no human name
        is set).

        Outputs:
        - ``"total_mass"``           → ``"Total mass"``
        - ``"samples[].density"``    → ``"Samples[].Density"`` (formula on a
          ParamSet inner key — applies to every row)
        - ``"samples[2].mass"``      → ``"Samples[2].Mass"`` (a single row)

        Used by save/test surfaces to turn validation- and computed-error
        keys into messages a user can read; the same shape is also handy for
        any other UI that needs a label for a stored field path.
        """
        from .param.param_set import ParamSet

        match = self._FIELD_KEY_RE.match(field_key)
        if match:
            outer_key, row_index, inner_key = match.groups()
            outer_spec = self.specs.get(outer_key)
            outer_name = (outer_spec.human_name if outer_spec else None) or outer_key
            inner_spec = (
                outer_spec.param_set.specs.get(inner_key)
                if isinstance(outer_spec, ParamSet) and outer_spec.param_set is not None
                else None
            )
            inner_name = (inner_spec.human_name if inner_spec else None) or inner_key
            return f"{outer_name}[{row_index}].{inner_name}"
        spec = self.specs.get(field_key)
        return (spec.human_name if spec else None) or field_key

    def format_field_errors(self, errors: dict[str, str]) -> list[str]:
        """Render a ``{field_key: message}`` map as a sorted list of
        ``"Label: message"`` strings (labels via :meth:`format_field_key`).

        Centralizes what every save/test surface used to do inline so the
        order and format are consistent across them.
        """
        return sorted(f"{self.format_field_key(key)}: {message}" for key, message in errors.items())

    def merge_computed(
        self,
        user_values: ConfigParamsDict,
        computed: ConfigParamsDict,
    ) -> ConfigParamsDict:
        """Merge the outer-scope computed dict into ``user_values`` and return
        the union.

        Per-row ParamSet computed cells are populated in-place by
        ``compute_values`` itself, so this only needs to handle outer-scope
        keys. The result is the single dict the caller persists.
        """
        result = copy.deepcopy(user_values) if user_values else {}
        for key, value in (computed or {}).items():
            spec = self.specs.get(key)
            if spec is None or spec.accepts_user_input:
                continue
            result[key] = value
        return result

    @staticmethod
    def diff_values(
        old: dict[str, Any] | None,
        new: dict[str, Any] | None,
    ) -> list[ConfigChangeEntry]:
        """Recursive diff producing one ConfigChangeEntry per leaf change.

        Field-path shape:
        - top-level scalar:        ``mass``
        - ParamSet item field:     ``samples[item_id=<uuid>].mass``
        - whole item add/remove:   ``samples[item_id=<uuid>]``

        Reorder = REMOVED + ADDED for the same ``__item_id``. Pure reorders
        (no inner field changes) produce no entries. Workflow-level events
        like form status transitions are appended by the caller.

        ParamSet diffing is delegated to ``ParamSet.diff_values`` (it owns the
        per-row identity model). This entry point only handles dispatch.
        """
        # ParamSet imported lazily: param_set.py imports ConfigSpecs at its
        # module top, so a top-level import here would form a cycle.
        from .param.param_set import ParamSet

        old = old or {}
        new = new or {}
        changes: list[ConfigChangeEntry] = []
        keys = set(old.keys()) | set(new.keys())
        for key in sorted(keys):
            old_val = old.get(key)
            new_val = new.get(key)
            if ConfigSpecs._is_paramset_value(old_val) or ConfigSpecs._is_paramset_value(new_val):
                changes.extend(ParamSet.diff_values(key, old_val, new_val))
            else:
                changes.extend(
                    ConfigSpecs.diff_scalar(key, old_val, new_val, key in old, key in new)
                )
        return changes

    @staticmethod
    def _is_paramset_value(value: Any) -> bool:
        if not isinstance(value, list) or not value:
            return False
        return all(isinstance(item, dict) for item in value)

    @staticmethod
    def diff_scalar(
        path: str,
        old_val: Any,
        new_val: Any,
        in_old: bool,
        in_new: bool,
    ) -> list[ConfigChangeEntry]:
        """Diff a single non-ParamSet value into 0 or 1 ConfigChangeEntry.

        Public so ParamSet.diff_values can reuse it for inner-field diffing.
        """
        if not in_old and in_new:
            return [
                ConfigChangeEntry(
                    field_path=path,
                    action=ConfigChangeAction.FIELD_CREATED,
                    old_value=None,
                    new_value=new_val,
                )
            ]
        if in_old and not in_new:
            return [
                ConfigChangeEntry(
                    field_path=path,
                    action=ConfigChangeAction.FIELD_DELETED,
                    old_value=old_val,
                    new_value=None,
                )
            ]
        if old_val != new_val:
            return [
                ConfigChangeEntry(
                    field_path=path,
                    action=ConfigChangeAction.FIELD_UPDATED,
                    old_value=old_val,
                    new_value=new_val,
                )
            ]
        return []

    def __len__(self) -> int:
        return len(self.specs)

    @classmethod
    def from_json(cls, dict_: dict[str, Any]) -> "ConfigSpecs":
        """Create a config specs from a json"""
        config_specs: dict[str, ParamSpec] = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_json(value)
        return cls(config_specs, _skip_key_validation=True)

    @classmethod
    def from_dto(cls, dict_: dict[str, ParamSpecDTO]) -> "ConfigSpecs":
        """Create a config specs from a dto"""
        config_specs: dict[str, ParamSpec] = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_dto(value)
        return cls(config_specs, _skip_key_validation=True)

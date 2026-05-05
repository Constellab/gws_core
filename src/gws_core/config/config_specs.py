import copy
from typing import Any, ClassVar

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.config_exceptions import MissingConfigsException, UnkownParamException
from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.param.param_spec_helper import ParamSpecHelper

from .param.param_spec import ParamSpec
from .param.param_types import ParamSpecDTO


class ConfigSpecs:
    """A typed schema (dict of ParamSpec) plus value-management helpers.

    The helpers (strip_computed_keys, validate_values, merge_computed,
    diff_values) operate on a values dict shaped by these specs.

    ITEM_ID_KEY is the reserved per-row key on ParamSet items. ParamSet.validate
    mints, preserves, and restores it; nothing else in ConfigSpecs writes it.
    """

    ITEM_ID_KEY: ClassVar[str] = "__item_id"

    specs: dict[str, ParamSpec]

    def __init__(self, specs: dict[str, ParamSpec] | None = None) -> None:
        """Define the spec of a task or a view
        Example:
        ConfigSpecs({
            "param1": IntParam(human_name="Param 1", default_value=1),
            "param2": StrParam(human_name="Param 2", default_value="Hello")
        })

        :param specs: _description_, defaults to None
        :type specs: Dict[str, ParamSpec], optional
        """
        if specs is None:
            specs = {}

        self.specs = specs

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
        if spec_name in self.specs:
            raise Exception(f"The spec {spec_name} already exists")
        self.specs[spec_name] = spec

    def add_or_update_spec(self, spec_name: str, spec: ParamSpec) -> None:
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
        if self.specs is None:
            return True

        for key, spec in self.specs.items():
            # System-derived params (e.g. ComputedParam) are never required from the user.
            if not spec.accepts_user_input:
                continue
            if not spec.optional and param_values.get(key, None) is None:
                return False

        return True

    def check_config_specs(self) -> None:
        """Check that the config specs are valid.

        Validates spec types and delegates to ComputedParam for cycle detection
        and reference validation across computed expressions.
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

        from gws_core.config.param.computed.computed_param import ComputedParam

        ComputedParam.check_graph(self)

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

        Thin delegator to ComputedParam.compute_all — see that method for the
        full contract.
        """
        from gws_core.config.param.computed.computed_param import ComputedParam

        return ComputedParam.compute_all(self, values, evaluator)

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

    def validate_values(self, values: ConfigParamsDict) -> ConfigParamsDict:
        """Run leaf-level ``ParamSpec.validate(...)`` on every provided value.

        Lenient: missing mandatories DO NOT raise (use ``mandatory_values_are_set``
        as a separate gate when required). Returns the reshaped dict — for
        ParamSets, ``ParamSet.validate`` mints ``__item_id`` per row and the
        result carries it back.

        ParamSet rows are re-validated through the spec to keep identity
        reconciliation in one place; non-ParamSet specs validate in place.
        """
        if not values:
            return {} if values is None else values

        result: ConfigParamsDict = {}
        for key, value in values.items():
            spec = self.specs.get(key)
            if spec is None or not spec.accepts_user_input:
                result[key] = value
                continue
            if value is None:
                result[key] = None
                continue
            # ParamSet.validate strips/mints/restores __item_id per row; other
            # specs validate the value as-is. No type discrimination needed.
            result[key] = spec.validate(value)
        return result

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
        return cls(config_specs)

    @classmethod
    def from_dto(cls, dict_: dict[str, ParamSpecDTO]) -> "ConfigSpecs":
        """Create a config specs from a dto"""
        config_specs: dict[str, ParamSpec] = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_dto(value)
        return cls(config_specs)

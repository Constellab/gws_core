from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import TypedDict

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.computed.computed_param_evaluator import (
    ComputedParamEvaluationError,
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import (
    ParamSpecDTO,
    ParamSpecType,
    ParamSpecVisibilty,
)
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

if TYPE_CHECKING:
    from gws_core.config.config_specs import ConfigSpecs

ComputedParamResultType = Literal["int", "float", "str", "bool"]


class ComputedParamAdditionalInfo(TypedDict):
    expression: str
    result_type: ComputedParamResultType


@param_spec_decorator(label="Computed", type_=ParamSpecCategory.COMPUTED)
class ComputedParam(ParamSpec):
    """Read-only param whose value is derived from other params via an expression.

    The user cannot submit a value for a ComputedParam. The value is recomputed
    on every save and on every read by ConfigSpecs.compute_values(...).
    """

    additional_info: ComputedParamAdditionalInfo

    def __init__(
        self,
        expression: str,
        result_type: ComputedParamResultType,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
    ) -> None:
        if not isinstance(expression, str) or not expression.strip():
            raise BadRequestException("ComputedParam.expression must be a non-empty string")
        if result_type not in ("int", "float", "str", "bool"):
            raise BadRequestException(
                f"ComputedParam.result_type must be one of int|float|str|bool, got '{result_type}'"
            )

        self.additional_info = {
            "expression": expression,
            "result_type": result_type,
        }
        super().__init__(
            default_value=None,
            optional=True,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @property
    def accepts_user_input(self) -> bool:
        return False

    def get_default_value(self) -> Any:
        return None

    def validate(self, value: Any) -> Any:
        # Defensive: clients must not write to a computed param. The input pass
        # in ConfigSpecs strips it before validation; we still raise here to catch
        # bugs that bypass the input pass.
        if value is not None:
            raise BadRequestException(
                "ComputedParam values are derived; submitting a value is not allowed"
            )
        return None

    @property
    def expression(self) -> str:
        return self.additional_info["expression"]

    @property
    def result_type(self) -> ComputedParamResultType:
        return self.additional_info["result_type"]

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.COMPUTED

    @classmethod
    def empty(cls) -> ComputedParam:
        # Placeholder used by load_from_dto before fields are populated. The real
        # expression and result_type come from spec_dto.additional_info.
        instance = cls.__new__(cls)
        instance.additional_info = {"expression": "0", "result_type": "float"}
        instance.default_value = None
        instance.optional = True
        instance.visibility = "public"
        instance.human_name = None
        instance.short_description = None
        return instance

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> ComputedParam:
        param_spec: ComputedParam = super().load_from_dto(spec_dto, validate=validate)
        info = spec_dto.additional_info or {}
        if "expression" not in info or "result_type" not in info:
            raise BadRequestException(
                "ComputedParam DTO is missing 'expression' or 'result_type' in additional_info"
            )
        param_spec.additional_info = {
            "expression": info["expression"],
            "result_type": info["result_type"],
        }
        # ComputedParam is always optional and never accepts user input
        param_spec.optional = True
        param_spec.default_value = None
        return param_spec

    @classmethod
    def get_default_value_param_spec(cls) -> ParamSpec:
        from gws_core.config.param.param_spec import StrParam

        return StrParam(optional=True)

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        from gws_core.config.param.param_spec import StrParam

        return {
            "expression": StrParam(human_name="Expression").to_dto(),
            "result_type": StrParam(
                human_name="Result type",
                allowed_values=["int", "float", "str", "bool"],
            ).to_dto(),
        }

    # --------- ConfigSpecs integration ---------------------------------------
    #
    # The two class methods below own everything ComputedParam-specific in the
    # ConfigSpecs evaluation/validation pipeline. ConfigSpecs delegates to them
    # so it does not need to know about expressions, evaluators, or graphs.

    @classmethod
    def check_graph(cls, specs: ConfigSpecs) -> None:
        """Validate ComputedParam references and reject cycles in `specs`.

        Builds the dependency graph across ComputedParam expressions, rejects
        references to keys not in `specs`, and runs Kahn's algorithm to detect
        cycles. Called from ConfigSpecs.check_config_specs.
        """
        deps = cls._build_dep_graph(specs)
        if not deps:
            return

        # Only computed-on-computed edges can form a cycle, so restrict to those.
        computed_only_deps = {k: {d for d in v if d in deps} for k, v in deps.items()}
        in_degree = {k: len(v) for k, v in computed_only_deps.items()}
        ready = [k for k, n in in_degree.items() if n == 0]
        resolved: set[str] = set()
        while ready:
            node = ready.pop()
            resolved.add(node)
            for other, other_deps in computed_only_deps.items():
                if node in other_deps and other not in resolved:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        ready.append(other)

        if len(resolved) != len(computed_only_deps):
            unresolved = sorted(set(computed_only_deps.keys()) - resolved)
            raise BadRequestException(
                f"Cycle detected in ComputedParam expressions among keys: {', '.join(unresolved)}"
            )

    @classmethod
    def _build_dep_graph(cls, specs: ConfigSpecs) -> dict[str, set[str]]:
        """Return computed_key -> referenced keys, raising on unknown refs."""
        deps: dict[str, set[str]] = {}
        for key, spec in specs.specs.items():
            if not isinstance(spec, cls):
                continue
            refs = ConfigSpecsEvaluator.extract_referenced_keys(spec.expression)
            for ref in refs:
                if ref not in specs.specs:
                    raise BadRequestException(
                        f"ComputedParam '{key}' references unknown key '{ref}'"
                    )
            deps[key] = refs
        return deps

    @classmethod
    def compute_all(
        cls,
        specs: ConfigSpecs,
        values: ConfigParamsDict,
        evaluator: ConfigSpecsEvaluator | None = None,
    ) -> tuple[ConfigParamsDict, dict[str, str]]:
        """Evaluate every ComputedParam in `specs` against `values`.

        - Returns (computed_values, errors_by_key).
        - computed_values has one entry per ComputedParam at the outer scope of
          `specs` (None when evaluation failed).
        - errors_by_key has a human-readable message for each failed entry.
          Inner-scope (ParamSet) errors use the path `<paramset_key>[].<field>`.
        - Per-row formulas inside ParamSets are evaluated first and mutated
          back into `values` so outer-scope formulas see fully-populated rows.
        - Outer-scope formulas evaluate in dependency order; cycle detection at
          check_graph time guarantees the resolution loop terminates.
        """
        evaluator = evaluator or ConfigSpecsEvaluator()
        computed: ConfigParamsDict = {}
        errors: dict[str, str] = {}

        cls._evaluate_paramset_rows(specs, values, evaluator, errors)
        cls._evaluate_outer_scope(specs, values, evaluator, computed, errors)

        return computed, errors

    @classmethod
    def _evaluate_paramset_rows(
        cls,
        specs: ConfigSpecs,
        values: ConfigParamsDict,
        evaluator: ConfigSpecsEvaluator,
        errors: dict[str, str],
    ) -> None:
        """Mutate ParamSet rows in-place to populate inner ComputedParam cells."""
        for key, spec in specs.specs.items():
            if not isinstance(spec, ParamSet) or spec.param_set is None:
                continue

            inner_computed = [(k, s) for k, s in spec.param_set.specs.items() if isinstance(s, cls)]
            if not inner_computed:
                continue

            for row in values.get(key) or []:
                for inner_key, inner_spec in inner_computed:
                    try:
                        raw = evaluator.evaluate(inner_spec.expression, row)
                        row[inner_key] = ConfigSpecsEvaluator.coerce_result(
                            raw, inner_spec.result_type
                        )
                    except ComputedParamEvaluationError as err:
                        row[inner_key] = None
                        errors[f"{key}[].{inner_key}"] = str(err)

    @classmethod
    def _evaluate_outer_scope(
        cls,
        specs: ConfigSpecs,
        values: ConfigParamsDict,
        evaluator: ConfigSpecsEvaluator,
        computed: ConfigParamsDict,
        errors: dict[str, str],
    ) -> None:
        """Resolve outer-scope ComputedParam keys in dependency order."""
        paramset_rows: dict[str, list[dict[str, Any]]] = {
            k: (values.get(k) or []) for k, s in specs.specs.items() if isinstance(s, ParamSet)
        }

        # Scope starts with non-computed values; computed entries fill in as
        # they evaluate so a computed-of-computed sees the upstream value.
        scope: dict[str, Any] = {
            k: v
            for k, v in values.items()
            if k in specs.specs and not isinstance(specs.specs[k], cls)
        }

        remaining = {k for k, s in specs.specs.items() if isinstance(s, cls)}
        while remaining:
            progressed = False
            for key in list(remaining):
                spec: ComputedParam = specs.specs[key]
                refs = ConfigSpecsEvaluator.extract_referenced_keys(spec.expression)
                if {r for r in refs if r in remaining and r != key}:
                    continue

                try:
                    raw = evaluator.evaluate(spec.expression, scope, paramset_rows=paramset_rows)
                    value = ConfigSpecsEvaluator.coerce_result(raw, spec.result_type)
                except ComputedParamEvaluationError as err:
                    value = None
                    errors[key] = str(err)

                computed[key] = value
                scope[key] = value
                remaining.discard(key)
                progressed = True

            if not progressed:
                # Safety net: check_graph should have caught any cycle. If we
                # land here, surface the unresolved keys as errors so the
                # result dict still contains every computed key.
                for key in remaining:
                    computed[key] = None
                    errors[key] = "Could not evaluate (unresolved dependency)"
                return

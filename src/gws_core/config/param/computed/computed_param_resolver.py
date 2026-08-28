from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.computed.computed_param_evaluator import (
    ComputedParamEvaluationError,
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_set import ParamSet

if TYPE_CHECKING:
    from gws_core.config.config_specs import ConfigSpecs
    from gws_core.config.param.computed.computed_param import ComputedParam


class ComputedParamResolver:
    """Evaluates every ComputedParam in a ConfigSpecs against a values dict.

    Owns the evaluation pipeline that ConfigSpecs.compute_values delegates to.
    Kept separate from ComputedParam (which is just a ParamSpec) because the
    concern is cross-spec: per-row formulas inside a ParamSet may reference
    outer-scope values via `@@name`, outer formulas may aggregate inner
    ComputedParams via `@key[].field`, so the two scopes evaluate in a single
    cross-scope topological order rather than as two independent passes.
    """

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
        - Per-row formulas inside ParamSets are mutated back into `values` so
          outer-scope aggregates see fully-populated rows.
        - Evaluation order is a single cross-scope topological resolution loop;
          cycle detection at check time guarantees the loop terminates.
        """
        evaluator = evaluator or ConfigSpecsEvaluator()
        computed: ConfigParamsDict = {}
        errors: dict[str, str] = {}

        outer_computed, inner_computed = cls._collect_computed_specs(specs)

        paramset_rows: dict[str, list[dict[str, Any]]] = {
            k: (values.get(k) or [])
            for k, s in specs.specs.items()
            if isinstance(s, ParamSet)
        }
        paramset_keys = set(paramset_rows)

        # Outer scope starts with non-computed outer values; computed entries
        # fill in as they evaluate so an inner row reading `@@x` (where x is an
        # outer ComputedParam) sees the upstream value.
        outer_scope: dict[str, Any] = {
            k: v
            for k, v in values.items()
            if k in specs.specs and k not in outer_computed
        }

        pending_outer: set[str] = set(outer_computed)
        pending_inner: set[tuple[str, str]] = {
            (psk, ik) for psk, inners in inner_computed.items() for ik in inners
        }

        while pending_outer or pending_inner:
            progressed = False

            for key in list(pending_outer):
                spec = outer_computed[key]
                if not cls._outer_node_is_ready(
                    spec.expression, key, pending_outer, pending_inner, inner_computed
                ):
                    continue

                value = cls._eval_outer_node(
                    spec, outer_scope, paramset_rows, paramset_keys, evaluator, errors, key
                )
                computed[key] = value
                outer_scope[key] = value
                pending_outer.discard(key)
                progressed = True

            for psk_ik in list(pending_inner):
                psk, ik = psk_ik
                spec = inner_computed[psk][ik]
                if not cls._inner_node_is_ready(
                    spec.expression, psk, ik, pending_outer, pending_inner
                ):
                    continue

                for row in values.get(psk) or []:
                    cls._eval_inner_row(
                        spec, row, outer_scope, evaluator, errors, psk, ik
                    )
                pending_inner.discard(psk_ik)
                progressed = True

            if not progressed:
                # Safety net: check should have caught any cycle. If we land
                # here, surface the unresolved keys as errors so the result
                # dict still contains every outer computed key.
                cls._mark_unresolved(computed, errors, pending_outer, pending_inner)
                return computed, errors

        return computed, errors

    @staticmethod
    def _collect_computed_specs(
        specs: ConfigSpecs,
    ) -> tuple[dict[str, ComputedParam], dict[str, dict[str, ComputedParam]]]:
        """Collect every ComputedParam of `specs`, split by scope.

        :return: a tuple ``(outer_computed, inner_computed)`` where
            ``outer_computed`` maps an outer key to its ComputedParam and
            ``inner_computed`` maps a ParamSet key to its own
            inner_key -> ComputedParam map. ParamSets holding no inner
            ComputedParam are dropped.
        """
        from gws_core.config.param.computed.computed_param import ComputedParam  # noqa: PLC0415

        outer_computed: dict[str, ComputedParam] = {
            k: s for k, s in specs.specs.items() if isinstance(s, ComputedParam)
        }
        inner_computed: dict[str, dict[str, ComputedParam]] = {
            k: {
                ik: isp
                for ik, isp in s.param_set.specs.items()
                if isinstance(isp, ComputedParam)
            }
            for k, s in specs.specs.items()
            if isinstance(s, ParamSet) and s.param_set is not None
        }
        # Drop ParamSets with no inner computed fields.
        inner_computed = {k: v for k, v in inner_computed.items() if v}
        return outer_computed, inner_computed

    @staticmethod
    def _outer_node_is_ready(
        expression: str,
        key: str,
        pending_outer: set[str],
        pending_inner: set[tuple[str, str]],
        inner_computed: dict[str, dict[str, ComputedParam]],
    ) -> bool:
        """True when an outer ComputedParam can be evaluated now.

        It is ready once every dependency it needs has left the pending sets:
        - its same-scope outer refs (a self-reference is ignored, it cannot be
          satisfied and is rejected at check time);
        - every inner ComputedParam of the ParamSets it aggregates via
          `@key[].field` (otherwise the aggregate would see None placeholders).

        :param expression: the expression of the ComputedParam
        :param key: its own key, excluded from its own dependencies
        :param pending_outer: outer keys not yet evaluated
        :param pending_inner: (paramset_key, inner_key) pairs not yet evaluated
        :param inner_computed: ParamSet key -> (inner key -> ComputedParam)
        """
        same_refs = ConfigSpecsEvaluator.extract_referenced_keys(expression)
        # Same-scope outer deps must be resolved.
        if {r for r in same_refs if r in pending_outer and r != key}:
            return False
        # Inner ComputedParams aggregated by this outer formula must be
        # resolved (otherwise the aggregate would see None placeholders).
        for psk in ConfigSpecsEvaluator.referenced_paramset_keys(expression):
            for fld in inner_computed.get(psk, {}):
                if (psk, fld) in pending_inner:
                    return False
        return True

    @staticmethod
    def _inner_node_is_ready(
        expression: str,
        paramset_key: str,
        inner_key: str,
        pending_outer: set[str],
        pending_inner: set[tuple[str, str]],
    ) -> bool:
        """True when a per-row ComputedParam can be evaluated now.

        It is ready once every dependency it needs has left the pending sets:
        - its outer refs (`@@name`) must be evaluated before touching any row;
        - its same-scope refs inside the same ParamSet must already be written
          into the row dicts.

        :param expression: the expression of the ComputedParam
        :param paramset_key: key of the enclosing ParamSet
        :param inner_key: its own inner key, excluded from its dependencies
        :param pending_outer: outer keys not yet evaluated
        :param pending_inner: (paramset_key, inner_key) pairs not yet evaluated
        """
        # Inner-to-outer deps via @@name must be resolved before
        # touching any row of this formula.
        outer_refs = ConfigSpecsEvaluator.extract_referenced_outer_keys(expression)
        if any(r in pending_outer for r in outer_refs):
            return False
        # Inner-to-inner same-scope deps within this ParamSet must be
        # resolved first (the row dict must already contain them).
        same_refs = ConfigSpecsEvaluator.extract_referenced_keys(expression)
        return all(
            r == inner_key or (paramset_key, r) not in pending_inner for r in same_refs
        )

    @staticmethod
    def _mark_unresolved(
        computed: ConfigParamsDict,
        errors: dict[str, str],
        pending_outer: set[str],
        pending_inner: set[tuple[str, str]],
    ) -> None:
        """Record an "unresolved dependency" error for every node still pending.

        Outer keys also get a None entry in `computed` so the result dict keeps
        one entry per outer ComputedParam. Inner errors use the
        ``<paramset_key>[].<inner_key>`` path.
        """
        for key in pending_outer:
            computed[key] = None
            errors[key] = "Could not evaluate (unresolved dependency)"
        for psk, ik in pending_inner:
            errors[f"{psk}[].{ik}"] = "Could not evaluate (unresolved dependency)"

    @staticmethod
    def _has_unset_dependency(
        expression: str,
        scope: dict[str, Any],
        paramset_keys: set[str] | None = None,
        outer_keys: set[str] | None = None,
    ) -> bool:
        """True if any same-scope key referenced by `expression` is missing from
        `scope` or resolves to None.

        Used to skip evaluation of a ComputedParam whose inputs aren't filled in
        yet: the result is "no value yet", not an error, so we leave the cell
        None and record nothing in the errors dict.

        ParamSet keys (referenced via `@key[].field` aggregate sugar) are never
        treated as unset — an empty list is a valid input the aggregate helpers
        handle on their own — so callers pass them in ``paramset_keys``.
        Outer-scope refs (`@@name`) are gated separately at node-readiness time;
        they show up in ``extract_referenced_keys`` of nothing — but to keep
        this helper future-proof we also accept an ``outer_keys`` ignore set.
        """
        ignored_paramset = paramset_keys or set()
        ignored_outer = outer_keys or set()
        for ref in ConfigSpecsEvaluator.extract_referenced_keys(expression):
            if ref in ignored_paramset or ref in ignored_outer:
                continue
            if ref not in scope or scope.get(ref) is None:
                return True
        return False

    @classmethod
    def _eval_outer_node(
        cls,
        spec: ComputedParam,
        outer_scope: dict[str, Any],
        paramset_rows: dict[str, list[dict[str, Any]]],
        paramset_keys: set[str],
        evaluator: ConfigSpecsEvaluator,
        errors: dict[str, str],
        key: str,
    ) -> Any:
        """Evaluate a single outer-scope ComputedParam. Returns the computed
        value (None on unset deps or evaluation error). Mutates ``errors`` on
        a true evaluation failure (vs. a not-yet-filled input)."""
        if cls._has_unset_dependency(spec.expression, outer_scope, paramset_keys):
            return None
        try:
            raw = evaluator.evaluate(
                spec.expression, outer_scope, paramset_rows=paramset_rows
            )
            return ConfigSpecsEvaluator.normalize_result(raw)
        except ComputedParamEvaluationError as err:
            errors[key] = str(err)
            return None

    @classmethod
    def _eval_inner_row(
        cls,
        spec: ComputedParam,
        row: dict[str, Any],
        outer_scope: dict[str, Any],
        evaluator: ConfigSpecsEvaluator,
        errors: dict[str, str],
        paramset_key: str,
        inner_key: str,
    ) -> None:
        """Evaluate a single per-row ComputedParam against ``row`` (plus
        ``outer_scope`` for any `@@name` refs). Writes the result into
        ``row[inner_key]`` and records evaluation errors keyed as
        ``<paramset_key>[].<inner_key>`` (one entry overwrites another across
        rows — matches the prior per-row behavior)."""
        outer_refs = ConfigSpecsEvaluator.extract_referenced_outer_keys(spec.expression)
        if cls._has_unset_dependency(spec.expression, row, outer_keys=outer_refs):
            row[inner_key] = None
            return
        # If the formula references an outer key that's still None at this
        # point, treat it as "no value yet" (mirrors same-row handling).
        if any(outer_scope.get(r) is None for r in outer_refs):
            row[inner_key] = None
            return
        try:
            raw = evaluator.evaluate(
                spec.expression, row, outer_scope=outer_scope
            )
            row[inner_key] = ConfigSpecsEvaluator.normalize_result(raw)
        except ComputedParamEvaluationError as err:
            row[inner_key] = None
            errors[f"{paramset_key}[].{inner_key}"] = str(err)

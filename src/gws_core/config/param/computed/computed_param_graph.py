from __future__ import annotations

from typing import TYPE_CHECKING

from gws_core.config.param.computed.computed_param_evaluator import (
    ComputedParamEvaluationError,
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_set import ParamSet
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

if TYPE_CHECKING:
    from gws_core.config.config_specs import ConfigSpecs
    from gws_core.config.param.computed.computed_param import ComputedParam


class ComputedParamGraphChecker:
    """Validates ComputedParam references and rejects cycles across a ConfigSpecs.

    Operates on a whole ConfigSpecs (and recursively on the inner specs of any
    ParamSet it contains). Builds the dependency graph implied by every
    ComputedParam expression, rejects references to unknown keys, and runs
    Kahn's algorithm to detect cycles — both within a single scope and across
    inner/outer scope boundaries (when an inner ParamSet formula uses `@@name`
    to reach the enclosing scope).

    Lives outside ComputedParam because the concern is cross-spec, not per-spec.
    """

    @classmethod
    def check(
        cls,
        specs: ConfigSpecs,
        scope_label: str | None = None,
        outer_specs: ConfigSpecs | None = None,
    ) -> None:
        """Validate ComputedParam references and reject cycles in `specs`.

        Recurses into ParamSet inner specs so per-row ComputedParams are
        validated too. When recursing, the enclosing ConfigSpecs is passed as
        ``outer_specs`` so any `@@name` reference can be checked against it.

        `scope_label` names the enclosing ParamSet (used to make error messages
        point at the right place). Called from
        ConfigSpecs.check_config_specs at the top level (outer_specs is None
        there); when not None, this is a recursive call from inside a ParamSet
        and the cross-scope cycle pass is suppressed until we unwind to the top.
        """
        for key, spec in specs.specs.items():
            if isinstance(spec, ParamSet) and spec.param_set is not None:
                cls.check(
                    spec.param_set,
                    scope_label=f"ParamSet '{key}'",
                    outer_specs=specs,
                )

        deps = cls._build_dep_graph(specs, scope_label, outer_specs=outer_specs)
        if deps:
            # Only computed-on-computed edges can form a (same-scope) cycle.
            computed_only_deps = {k: {d for d in v if d in deps} for k, v in deps.items()}
            resolved = cls._resolve_dependencies(computed_only_deps)

            if len(resolved) != len(computed_only_deps):
                unresolved = sorted(set(computed_only_deps.keys()) - resolved)
                location = f" inside {scope_label}" if scope_label else ""
                raise BadRequestException(
                    f"Cycle detected in ComputedParam expressions{location} "
                    f"among keys: {', '.join(unresolved)}"
                )

        # Cross-scope cycle detection runs once, at the top-level call. An
        # outer-scope formula that aggregates an inner ComputedParam and an
        # inner formula that reads an outer ComputedParam via `@@` can form a
        # cycle that the per-scope passes above cannot see.
        if outer_specs is None:
            cls._check_cross_scope_cycles(specs)

    @classmethod
    def _build_dep_graph(
        cls,
        specs: ConfigSpecs,
        scope_label: str | None = None,
        outer_specs: ConfigSpecs | None = None,
    ) -> dict[str, set[str]]:
        """Return computed_key -> same-scope referenced keys, raising on
        unknown refs (same-scope or outer-scope).
        """
        from gws_core.config.param.computed.computed_param import ComputedParam  # noqa: PLC0415

        deps: dict[str, set[str]] = {}
        for key, spec in specs.specs.items():
            if not isinstance(spec, ComputedParam):
                continue
            try:
                ConfigSpecsEvaluator.check_expression_syntax(spec.expression)
            except ComputedParamEvaluationError as err:
                location = f" inside {scope_label}" if scope_label else ""
                raise BadRequestException(
                    f"ComputedParam '{key}'{location} has an invalid expression: {err}"
                ) from err

            same_refs = ConfigSpecsEvaluator.extract_referenced_keys(spec.expression)
            for ref in same_refs:
                if ref not in specs.specs:
                    location = f" inside {scope_label}" if scope_label else ""
                    raise BadRequestException(
                        f"ComputedParam '{key}'{location} references unknown key '{ref}'"
                    )

            outer_refs = ConfigSpecsEvaluator.extract_referenced_outer_keys(spec.expression)
            if outer_refs:
                if outer_specs is None:
                    raise BadRequestException(
                        f"ComputedParam '{key}' uses outer reference "
                        f"'@@{sorted(outer_refs)[0]}'; outer references "
                        f"('@@name') are only valid inside a ParamSet."
                    )
                for ref in outer_refs:
                    if ref not in outer_specs.specs:
                        location = f" inside {scope_label}" if scope_label else ""
                        raise BadRequestException(
                            f"ComputedParam '{key}'{location} references "
                            f"unknown outer key '@@{ref}'"
                        )

            deps[key] = same_refs
        return deps

    @classmethod
    def _check_cross_scope_cycles(cls, specs: ConfigSpecs) -> None:
        """Detect cycles that cross scopes: outer ComputedParam → inner
        ComputedParam (via aggregate) → outer ComputedParam (via `@@`) chains.

        Builds a unified graph where each node is either an outer ComputedParam
        key or an `<paramset_key>[].<inner_key>` inner node (one per inner
        ComputedParam field, not per row — formulas are identical across rows).
        Edges run in the "depends on" direction.
        """
        outer_computed, inner_computed = cls._collect_computed_specs(specs)

        nodes: set[str] = set(outer_computed)
        for psk, inners in inner_computed.items():
            for fld in inners:
                nodes.add(cls._inner_node(psk, fld))

        if len(nodes) <= 1:
            return

        depends = cls._build_cross_scope_depends(outer_computed, inner_computed, nodes)
        resolved = cls._resolve_dependencies(depends)

        if len(resolved) != len(depends):
            unresolved = sorted(set(depends) - resolved)
            raise BadRequestException(
                "Cycle detected across ComputedParam scopes among: "
                + ", ".join(unresolved)
            )

    @staticmethod
    def _inner_node(paramset_key: str, inner_key: str) -> str:
        """Name of the graph node standing for one inner ComputedParam field.

        There is one node per inner field, not per row, because the formula is
        identical across the rows of a ParamSet.
        """
        return f"{paramset_key}[].{inner_key}"

    @staticmethod
    def _collect_computed_specs(
        specs: ConfigSpecs,
    ) -> tuple[dict[str, ComputedParam], dict[str, dict[str, ComputedParam]]]:
        """Collect every ComputedParam of `specs`, split by scope.

        :return: a tuple ``(outer_computed, inner_computed)`` where
            ``outer_computed`` maps an outer key to its ComputedParam and
            ``inner_computed`` maps a ParamSet key to its own
            inner_key -> ComputedParam map. ParamSets holding no ComputedParam
            are dropped to keep the graph small.
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
        # Drop ParamSets with no inner ComputedParams to keep the graph small.
        inner_computed = {k: v for k, v in inner_computed.items() if v}
        return outer_computed, inner_computed

    @classmethod
    def _build_cross_scope_depends(
        cls,
        outer_computed: dict[str, ComputedParam],
        inner_computed: dict[str, dict[str, ComputedParam]],
        nodes: set[str],
    ) -> dict[str, set[str]]:
        """Build the unified cross-scope dependency graph.

        ``depends[X]`` is the set of nodes X depends on (they must resolve
        first). Node names are outer keys, or ``<paramset>[].<inner>`` for
        inner ComputedParams (see :meth:`_inner_node`).

        :param outer_computed: outer key -> ComputedParam
        :param inner_computed: ParamSet key -> (inner key -> ComputedParam)
        :param nodes: every node of the graph, used to seed empty dep sets
        """
        depends: dict[str, set[str]] = {n: set() for n in nodes}
        cls._add_outer_dependencies(depends, outer_computed, inner_computed)
        cls._add_inner_dependencies(depends, outer_computed, inner_computed)
        return depends

    @classmethod
    def _add_outer_dependencies(
        cls,
        depends: dict[str, set[str]],
        outer_computed: dict[str, ComputedParam],
        inner_computed: dict[str, dict[str, ComputedParam]],
    ) -> None:
        """Add the dependencies of every outer ComputedParam into `depends`."""
        for key, spec in outer_computed.items():
            expr = spec.expression
            # Outer-to-outer same-scope deps.
            for ref in ConfigSpecsEvaluator.extract_referenced_keys(expr):
                if ref in outer_computed and ref != key:
                    depends[key].add(ref)
            # Outer-to-inner deps via @paramset[].field aggregate sugar: the
            # aggregate result includes every inner field's value, so if that
            # field is itself a ComputedParam it must resolve first.
            for psk in ConfigSpecsEvaluator.referenced_paramset_keys(expr):
                for fld in inner_computed.get(psk, {}):
                    depends[key].add(cls._inner_node(psk, fld))

    @classmethod
    def _add_inner_dependencies(
        cls,
        depends: dict[str, set[str]],
        outer_computed: dict[str, ComputedParam],
        inner_computed: dict[str, dict[str, ComputedParam]],
    ) -> None:
        """Add the dependencies of every per-row ComputedParam into `depends`."""
        for psk, inners in inner_computed.items():
            for fld, spec in inners.items():
                node = cls._inner_node(psk, fld)
                expr = spec.expression
                # Inner-to-inner same-scope deps (within the same ParamSet).
                for ref in ConfigSpecsEvaluator.extract_referenced_keys(expr):
                    if ref in inners and ref != fld:
                        depends[node].add(cls._inner_node(psk, ref))
                # Inner-to-outer deps via @@name.
                for ref in ConfigSpecsEvaluator.extract_referenced_outer_keys(expr):
                    if ref in outer_computed:
                        depends[node].add(ref)

    @staticmethod
    def _resolve_dependencies(depends: dict[str, set[str]]) -> set[str]:
        """Run Kahn's algorithm over a "depends on" graph.

        :param depends: node -> set of nodes it depends on. Dependencies that
            are not themselves nodes of `depends` are ignored (they can never
            be part of a cycle).
        :return: the set of nodes that could be resolved. When it is smaller
            than `depends`, the remaining nodes form (or feed into) a cycle.
        """
        in_degree = {n: len(d) for n, d in depends.items()}
        ready = [n for n, deg in in_degree.items() if deg == 0]
        resolved: set[str] = set()
        while ready:
            node = ready.pop()
            resolved.add(node)
            for other, other_deps in depends.items():
                if node in other_deps and other not in resolved:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        ready.append(other)
        return resolved

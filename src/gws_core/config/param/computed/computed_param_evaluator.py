import ast
import re
from collections.abc import Callable, Sequence
from statistics import mean, median, stdev
from typing import Any

from simpleeval import (
    FunctionNotDefined,
    InvalidExpression,
    NameNotDefined,
    NumberTooHigh,
    SimpleEval,
)

# Internal function names the rewriter injects; never written by users.
_PARAMSET_AGG_FUNC_NAME = "__paramset_agg__"
_IF_FUNC_NAME = "__cp_if__"

# Field references are written with a leading `@` so they can never be confused
# with a (bare) function name. `@samples[].mass` is the ParamSet aggregate sugar
# (the list of `mass` values across the `samples` ParamSet); `@weight` is a
# plain field reference. Both are rewritten away before the expression reaches
# simpleeval, which then sees only plain identifiers resolved from `names`.
_PARAMSET_AGG_PATTERN = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)\[\]\.([A-Za-z_][A-Za-z0-9_]*)")
_FIELD_REF_PATTERN = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)")

# Matches `if(` since `if` is a Python keyword and would otherwise fail to parse.
# Word boundary on the left, then literal `if(`. Rewritten to a non-keyword name.
_IF_CALL_PATTERN = re.compile(r"\bif\s*\(")

# Bare identifiers allowed in a (rewritten) expression: the whitelisted function
# names plus the internal names the rewriter injects. Anything else bare is a
# field reference missing its `@` (or an undefined name) and is rejected.
_ALLOWED_BARE_NAMES = frozenset(
    {
        "sum", "mean", "median", "stddev", "min", "max", "count",
        "abs", "round", "sqrt", "pow", "concat",
        "if",  # written `if(...)`, rewritten away, but keep for clarity
        _PARAMSET_AGG_FUNC_NAME,
        _IF_FUNC_NAME,
    }
)


class ComputedParamEvaluationError(Exception):
    """Raised when a single ComputedParam expression fails to evaluate.

    Carries a human-readable message that the caller surfaces alongside the
    field. Evaluation of other computed fields keeps going.
    """


class ConfigSpecsEvaluator:
    """Evaluates ComputedParam expressions over a ConfigSpecs values dict.

    Wraps simpleeval with a whitelisted function table and the `@samples[].field`
    aggregate sugar (rewritten to a function call before evaluation). Field
    references are written `@field`; bare identifiers are function names.

    The evaluator is generic — not form-specific. It is injected into
    ConfigSpecs.compute_values so ConfigSpecs has no dependency on simpleeval.
    """

    _functions: dict[str, Callable[..., Any]]

    def __init__(self) -> None:
        self._functions = self._build_function_table()

    def evaluate(
        self,
        expression: str,
        scope: dict[str, Any],
        paramset_rows: dict[str, list[dict[str, Any]]] | None = None,
    ) -> Any:
        """Evaluate a single expression against the provided scope.

        :param expression: the expression source. Field references are written
            with a leading `@` (e.g. `@weight`, `@samples[].mass`).
        :param scope: identifier → value map. `@`-prefixed references in the
            expression resolve (after the `@` is stripped) from this dict.
        :param paramset_rows: paramset_key → list of row dicts. Used to resolve
            `@samples[].field` aggregate sugar at the outer scope. None or empty
            when evaluating per-row inside a ParamSet.
        :raises ComputedParamEvaluationError: on any evaluation failure.
        """
        self._assert_only_sigil_field_refs(expression)
        rewritten = _rewrite_expression(expression)

        rows = paramset_rows or {}

        def _paramset_agg(paramset_key: str, field: str) -> list[Any]:
            if paramset_key not in rows:
                raise ComputedParamEvaluationError(
                    f"Unknown ParamSet '{paramset_key}' referenced in '{paramset_key}[].{field}'"
                )
            return [row.get(field) for row in rows[paramset_key]]

        functions = {
            **self._functions,
            _PARAMSET_AGG_FUNC_NAME: _paramset_agg,
            _IF_FUNC_NAME: _if,
        }

        evaluator = SimpleEval(names=scope, functions=functions)

        try:
            return evaluator.eval(rewritten)
        except ZeroDivisionError as err:
            raise ComputedParamEvaluationError("Division by zero") from err
        except NameNotDefined as err:
            name = self._safe_name(err)
            raise ComputedParamEvaluationError(
                f"Unknown name '{name}'. Field references must be written as @{name}."
            ) from err
        except FunctionNotDefined as err:
            raise ComputedParamEvaluationError(
                f"Function not allowed: {self._safe_name(err)}"
            ) from err
        except InvalidExpression as err:
            raise ComputedParamEvaluationError(
                f"Invalid expression: {err}"
            ) from err
        except NumberTooHigh as err:
            raise ComputedParamEvaluationError(f"Number too high: {err}") from err
        except (TypeError, ValueError) as err:
            raise ComputedParamEvaluationError(str(err)) from err

    @staticmethod
    def normalize_result(value: Any) -> Any:
        """Validate that an evaluated value is a supported scalar type.

        Like a spreadsheet cell, a ComputedParam takes whatever type the formula
        produces — no declared type, no coercion. We only check the result is one
        of int / float / str / bool (None passes through, meaning "no value yet").
        Anything else (a list, dict, ...) is an error.

        :raises ComputedParamEvaluationError: if the value is not a supported type.
        """
        if value is None:
            return None
        # bool is a subclass of int, so it is covered; list it for clarity.
        if isinstance(value, (bool, int, float, str)):
            return value
        raise ComputedParamEvaluationError(
            f"Result must be a number, string or boolean, got {type(value).__name__}"
        )

    @staticmethod
    def extract_referenced_keys(expression: str) -> set[str]:
        """Return the set of ConfigSpecs keys referenced by the expression.

        A reference is anything written with a leading `@`:
        - `@weight` contributes the key `weight`.
        - `@samples[].mass` (ParamSet aggregate sugar) contributes the ParamSet
          key `samples` (not `mass`, which is an inner field of that ParamSet).

        Bare identifiers are function names, never references, so there is no
        whitelist to subtract and no ambiguity with a field named e.g. `sum`.
        Used by ComputedParam.check_graph() for reference and cycle checks.
        """
        # ParamSet aggregate references must be matched first; otherwise the
        # plain `@<name>` pattern would also match the `@samples` prefix and
        # we could not tell them apart from a scalar `@samples` reference.
        paramset_keys = ConfigSpecsEvaluator.referenced_paramset_keys(expression)
        without_aggregates = _PARAMSET_AGG_PATTERN.sub(" ", expression)
        scalar_keys = {m.group(1) for m in _FIELD_REF_PATTERN.finditer(without_aggregates)}
        return scalar_keys | paramset_keys

    @staticmethod
    def referenced_paramset_keys(expression: str) -> set[str]:
        """Return the ParamSet keys referenced via aggregate sugar
        (``@key[].field`` → ``key``). Empty when the expression uses no
        aggregates. Used to detect aggregate usage from outside the evaluator
        (e.g. to reject it inside a ParamSet row, where it is not allowed)."""
        return {m.group(1) for m in _PARAMSET_AGG_PATTERN.finditer(expression)}

    @staticmethod
    def _assert_only_sigil_field_refs(expression: str) -> None:
        """Reject bare identifiers used as values (not function calls).

        A value identifier in a ComputedParam expression must be `@`-prefixed.
        A bare one is a field reference that forgot its `@` — a bug, because it
        would not appear in the dependency graph (so it escapes cycle and
        unset-input checks). We make it a hard error rather than letting
        simpleeval silently resolve it from `names`. Function-call names are
        left alone here; simpleeval reports unknown ones (`FunctionNotDefined`).

        :raises ComputedParamEvaluationError: on a bare value reference or an
            otherwise unparsable expression.
        """
        rewritten = _rewrite_expression(expression)
        try:
            tree = ast.parse(rewritten, mode="eval")
        except SyntaxError as err:
            raise ComputedParamEvaluationError(f"Invalid expression: {err.msg}") from err

        # Names that appear as the callee of a Call are function names — skip.
        call_func_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        allowed = _ALLOWED_BARE_NAMES | call_func_names | ConfigSpecsEvaluator.extract_referenced_keys(
            expression
        )
        bare = sorted(
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id not in allowed
        )
        if bare:
            names = ", ".join(f"'{n}'" for n in bare)
            raise ComputedParamEvaluationError(
                f"Unknown name(s): {names}. Field references must be written with a "
                f"leading @ (e.g. @{bare[0]})."
            )

    @staticmethod
    def check_expression_syntax(expression: str) -> None:
        """Validate that the expression parses and uses only `@`-prefixed field
        references, without evaluating it.

        Lets the form-template editor lint a candidate expression before any
        values exist to run it against.

        :raises ComputedParamEvaluationError: if the expression is empty, does
            not parse, or contains a bare (un-``@``-ed) field reference.
        """
        if not isinstance(expression, str) or not expression.strip():
            raise ComputedParamEvaluationError("Expression must be a non-empty string")
        ConfigSpecsEvaluator._assert_only_sigil_field_refs(expression)

    @staticmethod
    def _safe_name(err: Exception) -> str:
        name = getattr(err, "name", None)
        if name:
            return str(name)
        func = getattr(err, "func_name", None)
        if func:
            return str(func)
        return str(err)

    @classmethod
    def _build_function_table(cls) -> dict[str, Callable[..., Any]]:
        return {
            # Numeric
            "sum": _safe_sum,
            "mean": _safe_mean,
            "median": _safe_median,
            "stddev": _safe_stddev,
            "min": _safe_min,
            "max": _safe_max,
            "count": _count,
            "abs": abs,
            "round": round,
            "sqrt": _sqrt,
            "pow": pow,
            # String
            "concat": _concat,
        }


def _rewrite_expression(expression: str) -> str:
    """Lower a ComputedParam expression to a plain simpleeval expression.

    Three rewrites, in order:
    1. `@key[].field` ParamSet aggregate sugar → a call to the internal
       aggregate function.
    2. remaining `@field` references → the bare identifier `field` (simpleeval
       resolves it from the injected `names` dict).
    3. `if(...)` → an internal function name (`if` is a Python keyword and would
       otherwise fail to parse).

    Step 1 must run before step 2 so the `@` of an aggregate is consumed there
    and not by the plain-reference rewrite.
    """
    rewritten = _PARAMSET_AGG_PATTERN.sub(
        lambda m: f"{_PARAMSET_AGG_FUNC_NAME}('{m.group(1)}', '{m.group(2)}')",
        expression,
    )
    rewritten = _FIELD_REF_PATTERN.sub(lambda m: m.group(1), rewritten)
    rewritten = _IF_CALL_PATTERN.sub(f"{_IF_FUNC_NAME}(", rewritten)
    return rewritten


# ---------- whitelisted function implementations ----------


def _flatten_numeric_args(args: Sequence[Any]) -> list[float]:
    """Accept either a single iterable of numbers, or many number args."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        items = [v for v in args[0] if v is not None]
    else:
        items = [v for v in args if v is not None]
    return items


def _safe_sum(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if not items:
        return 0
    return sum(items)


def _safe_mean(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if not items:
        raise ComputedParamEvaluationError("mean() of empty sequence")
    return mean(items)


def _safe_median(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if not items:
        raise ComputedParamEvaluationError("median() of empty sequence")
    return median(items)


def _safe_stddev(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if len(items) < 2:
        raise ComputedParamEvaluationError("stddev() requires at least two values")
    return stdev(items)


def _safe_min(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if not items:
        raise ComputedParamEvaluationError("min() of empty sequence")
    return min(items)


def _safe_max(*args: Any) -> Any:
    items = _flatten_numeric_args(args)
    if not items:
        raise ComputedParamEvaluationError("max() of empty sequence")
    return max(items)


def _count(*args: Any) -> int:
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        return len([v for v in args[0] if v is not None])
    return len([v for v in args if v is not None])


def _sqrt(value: Any) -> float:
    if value is None:
        raise ComputedParamEvaluationError("sqrt(None)")
    if value < 0:
        raise ComputedParamEvaluationError("sqrt of a negative number")
    return value**0.5


def _if(cond: Any, a: Any, b: Any) -> Any:
    return a if cond else b


def _concat(*args: Any, sep: str = "") -> str:
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        items = args[0]
    else:
        items = args
    return sep.join("" if v is None else str(v) for v in items)

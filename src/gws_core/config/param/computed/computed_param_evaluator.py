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

# Sentinel used to detect references to a key that exists but has no value yet.
# simpleeval surfaces this as a NameNotDefined; the evaluator turns it into a
# clean error message.
_PARAMSET_AGG_FUNC_NAME = "__paramset_agg__"
_IF_FUNC_NAME = "__cp_if__"

# Matches `<identifier>[].<identifier>` aggregate sugar for ParamSets.
# Replaced before evaluation with a call to the internal aggregate function.
_PARAMSET_AGG_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\[\]\.([A-Za-z_][A-Za-z0-9_]*)")

# Matches `if(` since `if` is a Python keyword and would otherwise fail to parse.
# Word boundary on the left, then literal `if(`. Rewritten to a non-keyword name.
_IF_CALL_PATTERN = re.compile(r"\bif\s*\(")


class ComputedParamEvaluationError(Exception):
    """Raised when a single ComputedParam expression fails to evaluate.

    Carries a human-readable message that the caller surfaces alongside the
    field. Evaluation of other computed fields keeps going.
    """


class ConfigSpecsEvaluator:
    """Evaluates ComputedParam expressions over a ConfigSpecs values dict.

    Wraps simpleeval with a whitelisted function table and the `samples[].field`
    aggregate sugar (rewritten to a function call before evaluation).

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

        :param expression: the expression source.
        :param scope: identifier → value map. Bare identifiers in the expression
            resolve from this dict.
        :param paramset_rows: paramset_key → list of row dicts. Used to resolve
            `samples[].field` aggregate sugar at the outer scope. None or empty
            when evaluating per-row inside a ParamSet.
        :raises ComputedParamEvaluationError: on any evaluation failure.
        """
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
            raise ComputedParamEvaluationError(
                f"Unknown reference: {self._safe_name(err)}"
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
    def coerce_result(value: Any, result_type: str) -> Any:
        """Coerce an evaluated value into the declared result_type.

        None passes through. Coercion errors raise ComputedParamEvaluationError.
        """
        if value is None:
            return None
        try:
            if result_type == "int":
                return int(value)
            if result_type == "float":
                return float(value)
            if result_type == "str":
                return str(value)
            if result_type == "bool":
                return bool(value)
        except (TypeError, ValueError) as err:
            raise ComputedParamEvaluationError(
                f"Cannot coerce result to {result_type}: {err}"
            ) from err
        raise ComputedParamEvaluationError(f"Unknown result_type '{result_type}'")

    @staticmethod
    def extract_referenced_keys(expression: str) -> set[str]:
        """Return the set of bare identifiers and ParamSet aggregate keys
        referenced by the expression.

        Used by ConfigSpecs.check_config_specs() for cycle detection. Function
        names from the whitelist are filtered out; ParamSet aggregate references
        like `samples[].mass` contribute the ParamSet key (`samples`).
        """
        rewritten = _rewrite_expression(expression)

        # Collect ParamSet keys referenced via aggregate sugar.
        paramset_keys = {m.group(1) for m in _PARAMSET_AGG_PATTERN.finditer(expression)}

        # Find bare identifiers in the rewritten expression. We walk the AST
        # rather than regex-matching because regex can't tell `mass` (a ref)
        # apart from `mass=` (a kwarg) reliably.
        import ast

        try:
            tree = ast.parse(rewritten, mode="eval")
        except SyntaxError:
            # Defer the syntax error to evaluation time.
            return paramset_keys

        whitelist = set(_BUILTIN_FUNCTION_NAMES) | {_PARAMSET_AGG_FUNC_NAME, _IF_FUNC_NAME}
        names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id not in whitelist:
                names.add(node.id)

        return names | paramset_keys

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
    """Apply both rewrites: paramset aggregate sugar and `if(...)` keyword guard."""
    rewritten = _PARAMSET_AGG_PATTERN.sub(
        lambda m: f"{_PARAMSET_AGG_FUNC_NAME}('{m.group(1)}', '{m.group(2)}')",
        expression,
    )
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


_BUILTIN_FUNCTION_NAMES = (
    "sum",
    "mean",
    "median",
    "stddev",
    "min",
    "max",
    "count",
    "abs",
    "round",
    "sqrt",
    "pow",
    "if",
    "concat",
)

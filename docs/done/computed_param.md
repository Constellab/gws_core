# `ComputedParam` — Available options & functions

**Brick:** `gws_core`
**Defined in:** [`src/gws_core/config/param/computed/computed_param.py`](../src/gws_core/config/param/computed/computed_param.py)
**Evaluator:** [`src/gws_core/config/param/computed/computed_param_evaluator.py`](../src/gws_core/config/param/computed/computed_param_evaluator.py)

`ComputedParam` is a `ParamSpec` subclass for read-only fields whose value is *derived* from other params via an expression — the form/task user never types a value into it. It is a first-class `ParamSpec`, so it lives directly inside a `ConfigSpecs` next to the user-input params; there is no separate "formulas" collection. Because it is an ordinary `ParamSpec`, it works anywhere `ConfigSpecs` is used: forms, tasks, views, protocols.

---

## 1. Constructor options

```python
ComputedParam(
    expression: str,
    result_type: Literal["int", "float", "str", "bool"],
    visibility: ParamSpecVisibilty = "public",
    human_name: str | None = None,
    short_description: str | None = None,
)
```

| Option | Required | Description |
|---|---|---|
| `expression` | yes | The formula to evaluate (see §3). Field references are written with a leading `@` (e.g. `@weight`, `@samples[].mass`). Must be a non-empty string — an empty/blank string raises `BadRequestException` at construction. |
| `result_type` | yes | The type the evaluated result is coerced to. One of `"int"`, `"float"`, `"str"`, `"bool"`. Any other value raises `BadRequestException`. The result is coerced with the corresponding Python builtin (`int()`, `float()`, `str()`, `bool()`); a coercion failure makes the field's value `None` with an error message attached. `None` always passes through uncoerced. |
| `visibility` | no | Standard `ParamSpec` visibility (`"public"` / `"protected"` / `"private"`). Same semantics as other params. |
| `human_name` | no | Display label for the UI. |
| `short_description` | no | Help text for the UI. |

Options that are **not** available / are forced:

- No `default_value` — it is always `None` (the value comes from the evaluator, not a default).
- No `optional` flag — it is always forced to `True` (a computed field can never be "missing").
- `expression` and `result_type` are stored under `additional_info` and round-trip through `to_dto()` / `load_from_dto()` like any other param's additional info, so a `ComputedParam` survives schema serialization (e.g. a published `FormTemplateVersion.content`).

---

## 2. Behavior / contract (how it differs from a normal `ParamSpec`)

| Member | Behavior |
|---|---|
| `accepts_user_input` | Returns `False`. **This is the single flag every `ConfigSpecs` consumer keys off of**: consumers skip such entries when prompting the user, when running mandatory-field checks, and when validating user-submitted input. |
| `get_default_value()` | Returns `None`. |
| `validate(value)` | Raises `BadRequestException` if a non-`None` value is submitted (defensive — clients must never write to a computed key). `ConfigSpecs.get_and_check_values()` already strips computed entries before validation; this guard catches code paths that bypass the input pass. Returns `None` for `None`. |
| `expression` (property) | The expression string. |
| `result_type` (property) | The declared result type. |
| Nesting | A `ComputedParam` is always a leaf. It cannot itself contain another `ComputedParam`. Referencing another `ComputedParam`'s key from an expression *is* allowed (computed-of-computed) — cycles among such references are rejected at `check_config_specs()` time. |

### Where it plugs into `ConfigSpecs`

- `ConfigSpecs.check_config_specs()` → delegates to `ComputedParam.check_graph(...)`: validates that every key referenced by every `ComputedParam.expression` actually exists in the specs, and runs a topological sort (Kahn's algorithm) over the computed-on-computed edges to reject cycles. Recurses into `ParamSet` inner specs. Runs at form-template publish and at `Task` class registration.
- `ConfigSpecs.get_and_check_values(values)` → sets computed entries to `None` on the input pass (treats them as not-supplied, never appends them to `missing_params`).
- `ConfigSpecs.mandatory_values_are_set(values)` / `get_default_values()` → skip computed entries (return `None` for them).
- `ConfigSpecs.compute_values(values, evaluator=None)` → delegates to `ComputedParam.compute_all(...)`, returns `(computed_values, errors_by_key)` (see §4).
- `ConfigSpecs.strip_computed_keys(values)` → drops keys whose `accepts_user_input is False`, recursing into `ParamSet` rows. Used defensively on the input side.
- `ConfigSpecs.build_config_params(values)` → after normal validation, calls `compute_values` (best-effort) and merges the results into the returned `ConfigParams`, so tasks/views see the computed value as just another key.
- `to_dto(skip_private)` → unchanged in shape, but the DTO carries `accepts_user_input` so the UI can render the entry read-only.

---

## 3. Expression language

Expressions are evaluated with the [`simpleeval`](https://pypi.org/project/simpleeval/) library — **never** Python's `eval()`. The grammar is deliberately small.

**Field references use a leading `@`.** `@weight` is the value of the `ConfigSpecs` key `weight`; bare identifiers (no `@`) are *only* function names. This removes any ambiguity — a field literally named `sum` is referenced as `@sum`, while `sum(...)` is still the aggregate function — and means the dependency analyzer (used for cycle detection and the "is this input filled in yet?" check) never has a blind spot. A bare identifier used as a value (a forgotten `@`) is a hard error, not a silent fallback.

### Allowed

- **Arithmetic:** `+`  `-`  `*`  `/`  `//`  `%`  `**`, parentheses.
- **Comparisons:** `==`  `!=`  `<`  `<=`  `>`  `>=`.
- **Boolean:** `and`  `or`  `not`.
- **Field references:** `@<key>` (e.g. `@weight`) resolves to the value of that `ConfigSpecs` key *in the same scope*.
- **ComputedParam references:** another `ComputedParam`'s key may be referenced the same way (`@subtotal`); cycles are rejected at `check_config_specs()`.
- **ParamSet aggregate sugar:** `@samples[].mass` resolves to the *list* of `mass` values across every item of the `samples` `ParamSet`. Only valid at the scope **containing** the `ParamSet` (not from inside a `ParamSet` row — there, sibling fields are referenced as `@field`). Pass it to `sum` / `mean` / `count` / etc.
- **Whitelisted functions** — see §3.1.

### Disallowed

Attribute access, subscripting beyond the `[]` aggregate sugar, function calls outside the whitelist, imports, lambdas, and bare (un-`@`-ed) value identifiers. Anything else surfaces as an evaluation error → that single computed value becomes `None` with an error message; other computed fields keep evaluating.

### 3.1 Whitelisted functions

Numeric aggregate functions accept **either** a single list (typically a `@samples[].field` aggregate) **or** any number of scalar arguments — and `None` items are dropped before the computation.

| Function | Signature | Notes |
|---|---|---|
| `sum` | `sum(list)` or `sum(a, b, …)` | Returns `0` for an empty input. |
| `mean` | `mean(list)` or `mean(a, b, …)` | Errors (→ `None` + message) on empty input. |
| `median` | `median(list)` or `median(a, b, …)` | Errors on empty input. |
| `stddev` | `stddev(list)` or `stddev(a, b, …)` | Sample standard deviation; requires **≥ 2** values, otherwise errors. |
| `min` | `min(list)` or `min(a, b, …)` | Errors on empty input. |
| `max` | `max(list)` or `max(a, b, …)` | Errors on empty input. |
| `count` | `count(list)` or `count(a, b, …)` | Number of non-`None` items. |
| `abs` | `abs(x)` | Python builtin. |
| `round` | `round(x, ndigits=0)` | Python builtin. |
| `sqrt` | `sqrt(x)` | Errors on `None` or a negative argument. |
| `pow` | `pow(base, exp)` | Python builtin. |
| `if` | `if(cond, a, b)` | Ternary: returns `a` if `cond` is truthy, else `b`. (Internally rewritten because `if` is a Python keyword — you still just write `if(...)`.) |
| `concat` | `concat(a, b, …)` or `concat(list)` or `concat(list, sep=", ")` | Concatenates string arguments. Accepts a list (e.g. `concat(@samples[].name)` joins all `name` values across a `ParamSet`) or any number of scalars (`concat(@first_name, " ", @last_name)`). Optional `sep=` separator for the list form. Non-string arguments are coerced via `str()`; `None` becomes `""`. |

---

## 4. Evaluation timing, errors & storage

Computed values are recomputed on **every save** and **on read** over the current `values`. `ConfigSpecs.compute_values(values, evaluator)` (→ `ComputedParam.compute_all`) returns:

- `computed_values` — one entry per outer-scope `ComputedParam` (`None` when that field could not be evaluated).
- `errors_by_key` — a human-readable message for each field that failed. Inner-scope (`ParamSet`) errors use the path `<paramset_key>[].<field>`.

Rules:

- **Per-field isolation.** A missing referenced field, a type mismatch, division by zero, an empty aggregate input, or a coercion failure makes *that one* computed value `None` and records an error for it — the other computed fields still evaluate.
- **Unset vs. error.** If an input a formula depends on simply isn't filled in yet, the result is `None` with **no** error recorded (it's "no value yet", not a failure). `ParamSet` aggregate references (`@samples[].field`) are never treated as unset — an empty list is a valid input the aggregate helpers handle themselves.
- **Errors never block.** They don't fail save and don't affect mandatory-field validation (computed fields are skipped there anyway).
- **Evaluation order.** Inside `ParamSet`s, per-row formulas are evaluated first and written back into the rows, so outer-scope formulas see fully-populated rows. Outer-scope formulas then evaluate in dependency order (cycle detection at `check_graph` time guarantees the loop terminates).
- **Stored.** In a `Form`, computed values are persisted in `Form.values` alongside user-input values under the same spec key — keeping them searchable through the same JSON-key filters and matching the "a form value is a form value" mental model. They're recomputed on every save, then merged into the persisted union dict. Reads return the stored values directly (the recompute-on-read property is kept as a dev/test invariant: `stored == recompute(values)`). Client-submitted values for computed keys are stripped before validation; clients never write them.

The `ConfigSpecsEvaluator` (a.k.a. the `simpleeval` wrapper) is generic and not form-specific. `ConfigSpecs.compute_values` builds one automatically if you don't pass one, so `ConfigSpecs` itself has no dependency on `simpleeval`.

---

## 5. Scoping inside `ParamSet`

A `ComputedParam` placed **inside** a `ParamSet`'s inner `ConfigSpecs` is evaluated **per row**, with `@field` references resolving to sibling fields *in that same row*. A `ComputedParam` at the **outer** scope cannot see individual `ParamSet` rows except via the `@samples[].field` aggregate sugar (which is, conversely, *not* valid inside a `ParamSet` row).

```python
ConfigSpecs({
    "samples": ParamSet(ConfigSpecs({
        "mass":     FloatParam(human_name="Mass (g)"),
        "volume":   FloatParam(human_name="Volume (mL)"),
        "density":  ComputedParam(expression="@mass / @volume",
                                  result_type="float"),   # per-row
    })),
    "total_mass": ComputedParam(expression="sum(@samples[].mass)",
                                result_type="float"),     # outer scope
})
```

---

## 6. Quick examples

```python
# Simple arithmetic over sibling fields
ComputedParam(expression="@weight / (@height ** 2)", result_type="float",
              human_name="BMI")

# Conditional
ComputedParam(expression="if(@score >= 50, \"pass\", \"fail\")", result_type="str",
              human_name="Result")

# Aggregate over a ParamSet (declared at the scope containing the ParamSet)
ComputedParam(expression="mean(@measurements[].value)", result_type="float",
              human_name="Average measurement")

# String concatenation with a separator
ComputedParam(expression="concat(@samples[].name, sep=\", \")", result_type="str",
              human_name="Sample list")

# A field whose key collides with a function name — referenced with @, no ambiguity
ConfigSpecs({
    "sum":         FloatParam(human_name="Reported sum"),
    "doubled_sum": ComputedParam(expression="@sum * 2", result_type="float"),
})

# Computed-of-computed (allowed; cycles rejected at check_config_specs())
ConfigSpecs({
    "a": FloatParam(),
    "b": FloatParam(),
    "sum_ab":     ComputedParam(expression="@a + @b", result_type="float"),
    "sum_ab_x2":  ComputedParam(expression="@sum_ab * 2", result_type="float"),
})
```

---

## 7. Validating an expression while authoring

The form-template editor can lint a candidate `ComputedParam` expression against a draft version's specs **before the param exists** (and before any form values are entered):

```
POST /form-template/{id}/version/{version_id}/computed-param/validate
body = { "expression": "@mass / @volume", "result_type": "float",
         "param_set_key": "samples", "key": "density" }
→ { "valid": true, "referenced_keys": ["mass", "volume"], "error": null }
```

- `param_set_key` (optional) — validate against that `ParamSet`'s inner specs (a per-row formula). Outer-scope aggregate sugar (`@key[].field`) is rejected in that case.
- `key` (optional) — the intended key of the param being authored/edited. Supply it when editing an existing computed param so the cycle check is meaningful (e.g. retargeting `density`'s expression to something that references `density`).
- Checks: the `result_type` is one of the four allowed values (enforced by the request schema), the expression is non-empty and parses, uses only `@`-prefixed value references, every referenced key exists in the target scope, and adding the param introduces no cycle. A failed check returns `valid: false` with a human-readable `error` (HTTP 200) rather than an HTTP error — it's a linter.

`ConfigSpecsEvaluator.extract_referenced_keys(expr)`, `ConfigSpecsEvaluator.check_expression_syntax(expr)`, and `ComputedParam.check_graph(specs)` are the reusable building blocks behind this route.

---

## 8. Using `ComputedParam` in a `Task`

A `Task` may declare `ComputedParam` entries in its `config_specs`. At execution time `task_runner` calls `ConfigSpecs.compute_values(...)` after building the input `ConfigParams`, so the resolved value is available in `Task.run(params, ...)` exactly like any other key — from the task author's perspective it is just a derived input.

Constraints:

- A task's `ComputedParam` may only reference **other keys in the same `ConfigSpecs`** — no external state, no resource references (those would break determinism).
- Cycle and reference-validity checks run at **`Task` class-registration time** via `check_config_specs()`, so schema bugs surface early instead of at run time.
- UI runners (Streamlit task runner, protocol UI) render `ComputedParam` as read-only and update the recomputed value live as inputs change.

# Form & FormTemplate — Feature Specification

**Status:** Draft
**Date:** 2026-04-29
**Brick:** `gws_core`

---

## 1. Overview

Add a form-creation feature, similar to Google Forms, integrated with the existing `ConfigSpecs` / `ParamSpec` system and embeddable inside Notes and NoteTemplates via a new rich text block.

Two top-level concepts:

- **`FormTemplate`** — a reusable, versioned definition of a form's schema (fields = `ConfigSpecs`).
- **`Form`** — an instance of a `FormTemplate` filled (or being filled) with values. Bound to a specific published version of a template.

Forms can also be embedded inside notes; in that context the parent note may "own" the form, in which case deletion cascades.

Formulas are integrated into `ConfigSpecs` as a new `ComputedParam` `ParamSpec` subclass — there is no parallel "formulas" collection. This means `ComputedParam` is also usable in any other `ConfigSpecs` consumer (tasks, views, protocols).

---

## 2. Goals & non-goals

### Goals (v1)

- CRUD + search for `FormTemplate`.
- CRUD + search for `Form`.
- Versioning of `FormTemplate` with `DRAFT` / `PUBLISHED` / `ARCHIVED` version states.
- A `Form` lifecycle: `DRAFT` → `SUBMITTED` (locked).
- Computed/formula fields inside templates (read-only at fill time), implemented as `ComputedParam` — a new `ParamSpec` subclass usable anywhere `ConfigSpecs` is used (forms, tasks, views, protocols).
- Two new rich text block types: `FORM_TEMPLATE` (note templates only) and `FORM` (notes only).
- Per-field modification audit log (who set what, when), with stable identity for `ParamSet` items.
- Cascade rules: forms owned by a note are deleted with it; referenced forms are not.

### Non-goals (v1)

- Public/anonymous share URLs.
- New `ParamSpec` types (e.g. `DateParam`, choice fields). Use existing types; revisit later.
- Sections / pages / display-only blocks inside the schema. Reuse `ConfigSpecs` as-is; extend it later if needed.
- Conditional fields ("show B if A == yes").
- Upgrading an existing `Form` to a newer template version.
- Roles / per-template permissions (any authenticated user can do anything for now).
- Email notifications, analytics, multi-language, response signatures.

---

## 3. Data model

### 3.1 `FormTemplate`

The "family" record. Tags and high-level metadata live here. The actual schema content lives in `FormTemplateVersion`.

| Column | Type | Notes |
|---|---|---|
| `id` | str (UUID, PK) | Standard `Model` id. |
| `name` | str | Required. Human-readable. |
| `description` | str (nullable) | Optional. |
| `is_archived` | bool, default `False` | Soft-archive flag. Hard delete is also supported (separate route) when no `Form` references the template. |
| `created_at`, `last_modified_at` | datetime | From `Model`. |
| `created_by`, `last_modified_by` | FK → `User` | From `ModelWithUser`. |

Tags attach via existing `EntityTag` mechanism with a new `TagEntityType.FORM_TEMPLATE`. Tags are at the `FormTemplate` level (shared across all versions). Propagable tags propagate to `Form` instances created from this template — see §3.5.

**Invariants:**
- At most one `DRAFT` version per template at any time. Enforced by a partial unique constraint on `gws_form_template_version` over `(template_id) WHERE status = 'DRAFT'`.
- Version numbers are unique per template. Enforced by a unique constraint on `(template_id, version)`.
- Hard delete (`DELETE /form-template/{id}`) is rejected if any `Form` references any version of this template. Use archive instead.

**Derived lookups (no FK column needed):**
- "Current draft version" = `SELECT * FROM form_template_version WHERE template_id = ? AND status = 'DRAFT'` (at most one row).
- "Current published version" = `SELECT * FROM form_template_version WHERE template_id = ? AND status = 'PUBLISHED' ORDER BY version DESC LIMIT 1`.

Both queries are O(1) given the indexes above. Denormalizing these into FK columns on `FormTemplate` is a future optimization if profiling shows a hotspot — not needed for v1.

### 3.2 `FormTemplateVersion`

Each row is a frozen schema snapshot once `PUBLISHED`.

| Column | Type | Notes |
|---|---|---|
| `id` | str (UUID, PK) | |
| `template_id` | FK → `FormTemplate` | |
| `version` | int | Monotonic per template. Assigned at publish time as `max(version)+1`. |
| `status` | enum `FormTemplateVersionStatus` | `DRAFT`, `PUBLISHED`, `ARCHIVED`. |
| `content` | JSON | Serialized `ConfigSpecs` (via `ConfigSpecs.to_dto()`). Includes `ComputedParam` entries for formulas (see §6). |
| `published_at` | datetime (nullable) | Set on `DRAFT → PUBLISHED`. |
| `published_by` | FK → `User` (nullable) | |
| `created_at`, `last_modified_at` | datetime | |
| `created_by`, `last_modified_by` | FK → `User` | |

**Lifecycle:**
- New template → automatically creates a `DRAFT` v1.
- `DRAFT` is freely editable.
- `DRAFT → PUBLISHED`: validates schema, freezes content, assigns `version = max+1`, becomes new `current_published_version_id`.
- `PUBLISHED → ARCHIVED`: forbids new `Form` creation from this version. Existing forms keep working.
- `PUBLISHED` is immutable. To change a published schema, create a new `DRAFT` (only allowed if no `DRAFT` currently exists for this template).
- A `DRAFT` can be deleted outright. A `PUBLISHED` version can only be `ARCHIVED`. An `ARCHIVED` version can be hard-deleted only if no `Form` references it.

**Why a separate version table (not just a `version` int on `FormTemplate`)?** Forms freeze at the version they were created from. We need every historical version queryable. This matches the question raised in §B5 of the design discussion — answer was (a).

### 3.3 `Form`

| Column | Type | Notes |
|---|---|---|
| `id` | str (UUID, PK) | |
| `name` | str | Defaults to `template.name` at creation. Editable. |
| `template_version_id` | FK → `FormTemplateVersion` | The frozen version this form was created from. |
| `status` | enum `FormStatus` | `DRAFT` (editable) or `SUBMITTED` (locked). |
| `submitted_at` | datetime (nullable) | Set on `DRAFT → SUBMITTED`. |
| `submitted_by` | FK → `User` (nullable) | |
| `values` | JSON | Current field values keyed by spec key — union of user-input values and computed values (see §6.7). ParamSet items carry stable `__item_id` (see §7). |
| `is_archived` | bool, default `False` | Soft-archive flag. Independent of status. |
| `created_at`, `last_modified_at` | datetime | |
| `created_by`, `last_modified_by` | FK → `User` | |

Tags attach via `EntityTag` with `TagEntityType.FORM`. Tags from the source `FormTemplate` propagate to the `Form` via the existing tag propagation system — see §3.5.

**Invariants:**
- A `Form` can only be created from a `PUBLISHED` `FormTemplateVersion`.
- A `SUBMITTED` form can be re-edited (status stays `SUBMITTED`, but every edit is logged in `FormSaveEvent`). This matches the C9 decision: re-edit allowed, status sticks. *Implementation note:* if we later want a stricter "lock", we can gate edits on a separate flag without changing status semantics.
- Archive is orthogonal to status (per C8 / G24): there is no `ARCHIVED` status; there's an `is_archived` boolean and a dedicated archive/unarchive route.

### 3.4 `FormSaveEvent`

Audit table — **one row per save event** (not per field). All changes that resulted from a single save call live in a JSON list inside the row. This matches the existing `Note.modifications` pattern and keeps row counts proportional to user activity, not to form size.

| Column | Type | Notes |
|---|---|---|
| `id` | str (UUID, PK) | |
| `form_id` | FK → `Form` (indexed) | |
| `user_id` | FK → `User` | The user that committed the save. |
| `created_at` | datetime | Save timestamp. |
| `changes` | JSON (list of `FormChangeEntry`) | Flat list of every leaf-level change in this save. See shape below. |

`FormChangeEntry` shape (one entry per change in `changes`):

```jsonc
{
  "field_path": "samples[item_id=ab12].mass",   // see §7
  "action": "FIELD_UPDATED",                    // see action enum below
  "old_value": 1.4,                             // JSON-serializable, nullable
  "new_value": 1.5                              // JSON-serializable, nullable
}
```

`action` enum (`FormChangeAction`): `FIELD_CREATED`, `FIELD_UPDATED`, `FIELD_DELETED`, `PARAMSET_ITEM_ADDED`, `PARAMSET_ITEM_REMOVED`, `STATUS_CHANGED`.

For `STATUS_CHANGED` entries the `field_path` is the literal string `"__status"` (reserved; cannot collide with a real `ConfigSpecs` key thanks to the leading underscores), `old_value` is the previous status, `new_value` is the new status. Status transitions are recorded as a regular entry in `changes` for uniformity rather than as a dedicated row.

Indexes:
- `(form_id, created_at DESC)` — main history query (paginated form timeline).
- `(user_id, created_at DESC)` — "what did user X do recently".
- A GIN/JSON index on `changes` is **not** added in v1. If field-path filter queries become hot, add `CREATE INDEX ... USING GIN ((changes jsonb_path_ops))` (Postgres) without a schema change.

Rows are **only** appended on Form save (per F19): we diff the saved `values` against the previous `values` and append one entry per changed leaf path / ParamSet item add-or-remove / status transition. If a save resulted in zero changes (the user clicked Save with no edits), no row is written. No entry is emitted for fields the user briefly touched then reverted before saving.

Compression note: a save changing N fields is now 1 row × N JSON entries instead of N rows. Per-row overhead (id, FKs, timestamp) is paid once per save; the JSON list scales linearly with the diff size. Realistic forms see 10–50× row reduction vs. one-row-per-change.

---

### 3.5 Tag propagation: `FormTemplate` → `Form`

`FormTemplate` is "navigable upstream" of any `Form` created from one of its versions, so it integrates with the existing `EntityNavigableModel` / `TagOriginType` propagation system rather than implementing a parallel one.

Concretely:

- A new `TagOriginType.FORM_TEMPLATE_PROPAGATED` enum entry is added (see [tag_dto.py:23](bricks/gws_core/src/gws_core/tag/tag_dto.py#L23)). The `origin_id` is the source `FormTemplate.id`.
- When a `Form` is created from a `FormTemplateVersion`, the `FormService` calls `EntityTagList.add_tags_and_propagate(...)` (or the equivalent — match the call shape used by `Note`/`Resource`) with the propagable tags from the source `FormTemplate`. Non-propagable tags are not copied.
- The `Form` record makes itself navigable from the `FormTemplate` (implements the existing `EntityNavigableModel` interface, exposing the `FormTemplate` as an upstream entity), so subsequent tag-propagation events on the `FormTemplate` (e.g. user adds a propagable tag via the tag controller) reach the existing `Form` rows automatically through the standard propagation walk.
- When a propagable tag is **removed** from a `FormTemplate`, the standard `delete_propagated_tags(...)` path removes it from downstream `Form`s as well, matching `Note`/`Resource` behavior.
- A user can still attach tags directly to a `Form` (`origin_type = USER`); these are independent of propagation and stay even if the template tag is removed.
- Tag propagation only flows `FormTemplate` → `Form`, not the reverse.

This keeps the form module from reimplementing tag inheritance and means the existing tag-impact-check routes (`/tag/check-propagation-add/...`) work for `FormTemplate` tags out of the box once `TagEntityType.FORM_TEMPLATE` and `TagEntityType.FORM` are registered.

---

## 4. Relationships & cascade rules

```
FormTemplate 1───* FormTemplateVersion 1───* Form 1───* FormSaveEvent
```

- Hard-deleting a `FormTemplate` is rejected if any `Form` references any of its versions (including across versions). Archive instead.
- Hard-deleting a `FormTemplateVersion`:
  - `DRAFT`: always allowed.
  - `PUBLISHED`: not allowed; must be archived first.
  - `ARCHIVED`: allowed iff no `Form` references it.
- Deleting a `Form` cascade-deletes its `FormSaveEvent` rows.
- Note ↔ Form ownership cascade: see §5.4.

---

## 5. Rich text integration

### 5.1 New block types

Two new entries in `RichTextBlockTypeStandard`:

- `FORM_TEMPLATE` — only valid inside a `NoteTemplate`. Cannot be filled.
- `FORM` — only valid inside a `Note`. Holds values.

Each block follows the existing pattern (`RichTextBlockDataBase` subclass + `@rich_text_block_decorator`), placed under `src/gws_core/impl/rich_text/block/rich_text_block_form_template.py` and `rich_text_block_form.py`.

### 5.2 `FORM_TEMPLATE` block payload

```jsonc
{
  "form_template_id": "uuid",
  "form_template_version_id": "uuid",   // pinned version at insertion time
  "display_name": "Sample collection"   // overridable label, defaults to template.name
}
```

Validation: the version referenced must be `PUBLISHED` at the time of insertion. If the version is later `ARCHIVED`, the block remains valid (it's frozen).

### 5.3 `FORM` block payload

```jsonc
{
  "form_id": "uuid",
  "is_owner": true,                     // true = this note created the form
  "display_name": "Sample collection"
}
```

`is_owner=true` is set when the note created the form (either by instantiating a `NoteTemplate` containing a `FORM_TEMPLATE` block, or by inserting a brand-new form into the note). `is_owner=false` is set when the user inserts a reference to an *existing* form created elsewhere.

A given `Form` has at most one owner block (DB-enforced at the application layer — see §5.4).

### 5.4 NoteTemplate → Note conversion (per E16)

When a `NoteTemplate` is instantiated as a `Note`:

1. For each `FORM_TEMPLATE` block in the template's content:
   1. Resolve the `form_template_version_id`. If it's `ARCHIVED`, fall back to `current_published_version_id` of the same template; if none, abort instantiation with a clear error.
   2. Create a new `Form` (status `DRAFT`, name = template.name) bound to that version.
   3. Replace the block in the new note's content with a `FORM` block carrying `form_id` of the new form and `is_owner=true`.
2. All other blocks copy over unchanged.

### 5.5 Inserting a `FORM` block directly into a note (per E17)

Two operations exposed to the UI:

- **Create a new form from a template** — picks a template, creates a `Form` (status `DRAFT`), inserts a `FORM` block with `is_owner=true`.
- **Reference an existing form** — picks an existing form (search by name/tag/template), inserts a `FORM` block with `is_owner=false`.

The same `Form` may appear in many notes via reference blocks. Edits are visible in all of them (it's the same row).

### 5.6 Cascade on note deletion (per E18)

When a `Note` is hard-deleted:

- For each `FORM` block in its content:
  - If `is_owner=true` **and** no other `Note` references the same `form_id` via a `FORM` block → delete the `Form` (cascade-deletes `FormSaveEvent`).
  - Otherwise → leave the `Form` in place. If we removed the only owner block but a non-owner reference remains, the form is now "orphaned of owner"; that's allowed.

The "no other Note references it" check is necessary because §5.5 lets users reference a form before its owning note is deleted.

### 5.7 Note rich-text modifications interaction

The existing `Note.modifications` field tracks block-level edits. Adding/removing a `FORM` block produces a standard `RichTextBlockModificationDTO` entry (CREATED / DELETED) — no change there. Edits to the *form's contents* are tracked separately in `FormSaveEvent`, not in the note's rich text modifications.

---

## 6. Formulas as `ComputedParam` (integrated into `ConfigSpecs`)

Formulas are first-class `ParamSpec` entries, not a parallel collection. This keeps a single source of truth for the schema, gives free DTO/JSON serialization, preserves field ordering for the UI, and supports per-row formulas inside `ParamSet`s.

### 6.1 New `ComputedParam` class

```python
@param_spec_decorator(type_=ParamSpecType.COMPUTED)
class ComputedParam(ParamSpec):
    """Read-only param whose value is derived from other params via an expression.

    The user cannot submit a value for a ComputedParam. The value is recomputed
    on every save and on every read by ConfigSpecs.compute_values(...).
    """
    expression: str
    result_type: Literal["int", "float", "str", "bool"]
```

Key contract points (different from a normal `ParamSpec`):

- `validate(value)` raises if a non-null value is submitted (defensive — clients must not write to it; the input pass strips it before validation).
- `get_default_value()` returns `None`. The real value comes from the evaluator.
- `optional` is forced to `True` and `accepts_user_input` (see §6.2) returns `False`.
- `to_dto()` serializes `expression` and `result_type` into `additional_info`. `load_from_dto` reverses it. The existing `ParamSpecHelper` mechanism handles registration once the new `ParamSpecType.COMPUTED` is registered.
- Cannot appear nested inside another `ComputedParam` (computed-of-computed is fine via key reference, but the spec entry itself is always a leaf).

### 6.2 Changes to `ParamSpec` base

Add one new property on `ParamSpec`:

```python
@property
def accepts_user_input(self) -> bool:
    """Whether this param expects a value supplied by the user.

    False means the value is determined by the system (currently: ComputedParam).
    Consumers should skip such entries when prompting users, when running
    mandatory-field checks, and when validating user-submitted input.
    """
    return True
```

`ComputedParam` overrides to `False`. Existing subclasses inherit the default. This is the **single flag every `ConfigSpecs` consumer keys off of** to decide whether to prompt the user for a value, validate user-submitted input, and require it in mandatory-field checks. The name is intentionally generic so future system-derived param types (e.g. server-set timestamps, resource-derived params) can reuse the same flag without renaming it.

### 6.3 Changes to `ConfigSpecs`

Two new methods, plus surgical edits to existing ones:

- `compute_values(values, evaluator) -> dict` — runs the evaluator over entries with `accepts_user_input=False`, returns a new dict including computed results. Called by the form service after input validation; can also be called by anyone holding a `ConfigSpecs`.
- `check_config_specs()` (existing) gains cycle detection across `ComputedParam.expression` references via topological sort. Runs at template publish and on `Task` registration.
- `get_and_check_values(param_values)` skips entries where `accepts_user_input=False` on the input pass (treats them as not-supplied; doesn't append them to `missing_params`).
- `mandatory_values_are_set(values)` skips entries where `accepts_user_input=False`.
- `all_config_are_optional()`, `has_visible_config_specs()`, `to_dto(skip_private)` — unchanged in shape, but the DTO carries `accepts_user_input` so the UI can render derived entries as read-only.
- `get_default_values()` returns `None` for entries where `accepts_user_input=False` (caller decides whether to display "—" or trigger evaluation).

### 6.4 Expression language

Implemented with `simpleeval` (per D13) — never `eval()`. Allowed:

- Arithmetic: `+ - * / // % **`, parentheses.
- Comparisons: `== != < <= > >=`.
- Boolean: `and or not`.
- Numeric functions: `sum`, `mean`, `median`, `stddev`, `min`, `max`, `count`, `abs`, `round(x, ndigits=0)`, `sqrt`, `pow`, `if(cond, a, b)`.
- String functions: `concat(a, b, ...)` — concatenates string arguments. Accepts a list (so `concat(samples[].name)` joins all `name` values across a ParamSet) or any number of scalars (`concat(first_name, " ", last_name)`). Optional separator via `concat(values, sep=", ")` for the list form. Non-string arguments are coerced via `str()`.
- Field references: a bare identifier (`weight`) resolves to the value of that `ConfigSpecs` key in the same scope.
- ParamSet aggregates: `samples[].mass` resolves to the list of `mass` values across all items in the `samples` ParamSet, suitable for passing to `sum`/`mean`/`median`/`stddev`/`min`/`max`/`count`. Only valid at the scope *containing* the ParamSet (not from inside the ParamSet itself, which uses bare identifiers for sibling fields).
- ComputedParam references: another `ComputedParam`'s key can be referenced; cycles are rejected at `check_config_specs()` time.

Disallowed: attribute access, subscripting beyond the `[]` aggregate sugar, function calls outside the whitelist, imports, lambdas.

### 6.5 Scoping inside `ParamSet`

A `ComputedParam` placed inside a `ParamSet`'s inner `ConfigSpecs` evaluates per-row, with bare identifiers resolving to sibling fields in the same row. A `ComputedParam` at the outer scope cannot see individual ParamSet rows except via the `samples[].field` aggregate sugar.

```python
ConfigSpecs({
    "samples": ParamSet(ConfigSpecs({
        "mass":     FloatParam(human_name="Mass (g)"),
        "volume":   FloatParam(human_name="Volume (mL)"),
        "density":  ComputedParam(expression="mass / volume",
                                  result_type="float"),   # per-row
    })),
    "total_mass": ComputedParam(expression="sum(samples[].mass)",
                                result_type="float"),     # outer scope
})
```

`ParamSet.validate(...)` runs the per-row evaluator after each dict is validated. The outer `ConfigSpecs.compute_values(...)` runs after all `ParamSet`s have been reconciled, so outer formulas see fully-populated rows.

### 6.6 Evaluator

`ConfigSpecsEvaluator` lives at `src/gws_core/config/param/computed/computed_param_evaluator.py` (generic — not form-specific). Wraps `simpleeval` with the whitelisted function table and the `[]` aggregate sugar. Injected into `ConfigSpecs.compute_values(...)` so `ConfigSpecs` itself doesn't depend on `simpleeval`.

### 6.7 Evaluation timing & errors

Computed at every form save (and on read) over the current `values`. Errors per D14:

- Missing referenced field, type mismatch, division by zero, empty aggregate input → that single computed result is `None` and an error message is returned alongside the field. Other computed fields keep evaluating.
- Errors do not block save and do not affect mandatory-field validation (computed fields are skipped in mandatory-check anyway).
- Computed values **are stored** in `Form.values` alongside user-input values, keyed by the same spec key. They're recomputed on every save, then merged into the union dict that gets persisted. This keeps computed fields searchable through the same JSON-key filters that user fields use, and matches the user's mental model ("a form value is a form value"). Reads return the stored values directly; the recompute-on-read property is preserved as a correctness invariant (assert `stored == recompute(values)` in dev/test).
- Client-submitted values for computed keys are stripped from `dto.values` before validation. Storage is the union of validated user values + freshly-computed values; clients never write to computed keys directly.

### 6.8 Allowing `ComputedParam` in tasks

Tasks may declare `ComputedParam` in their `config_specs`. At task execution time, `task_runner` calls `ConfigSpecs.compute_values(...)` after building the input `ConfigParams`, so the resolved value is available to `Task.run(params, ...)` exactly like any other key. From a task author's perspective, a computed param is just a derived input.

Constraints:

- A task's `ComputedParam` may only reference other keys in the same `ConfigSpecs` (no external state, no resource references — those would break determinism and require their own design).
- Cycle and reference-validity checks run at `Task` class-registration time via `check_config_specs()`, surfacing schema bugs early instead of at run time.
- The streamlit task runner UI and protocol UI render `ComputedParam` as read-only with the recomputed value updating live as inputs change.

### 6.9 Cross-cutting consumer audit (one-time PR)

Every existing place that iterates `ConfigSpecs.specs` needs a deliberate decision about entries where `accepts_user_input=False`. Audit list (from `grep build_config_params|get_and_check_values|mandatory_values_are_set`):

- `task/task_model.py`, `task/task_runner.py` — call `compute_values` after input validation; pass merged dict to `Task.run`.
- `process/process_model.py`, `protocol/protocol_service.py` — same as task runner; verify config display includes computed fields as read-only.
- `resource/view/view_runner.py`, `view_resource.py`, `mixed_views.py`, `multi_views.py` — views currently take user-supplied params; computed view params are unusual but harmless. Default behavior: support them, treat them like task params.
- `apps/streamlit/...` (`streamlit_task_runner.py`, agents, showcase pages) — UI must render computed entries as read-only with live recompute on input change.
- `impl/agent/...` (`env_agent.py`, `py_agent.py`, `agent_factory.py`) — agents accept user-provided code; computed params here are low-value but should not break. Verify they don't get prompted to the user.
- `config/param/dynamic_param.py` — dynamic params build a `ConfigSpecs` at runtime; verify it doesn't accidentally produce a `ComputedParam` it can't evaluate.
- `config/config.py` — central glue; the main place that needs the `compute_values` call inserted.
- `test/view_tester.py` — extend to pre-populate computed values when testing.

The migration is mechanical: each call site chooses one of `skip entries where !accepts_user_input`, `compute then include`, or `reject` (the latter only for places that genuinely cannot support them — none identified so far).

---

## 7. ParamSet identity & field paths

`ParamSet` produces `List[Dict[str, Any]]`. To track per-item edits across reorderings (per F22):

- Every dict in a `ParamSet` value carries a reserved `__item_id` (UUID v4 string), assigned by the server when the item is added.
- The id is preserved on edit/move. It's regenerated only if the client submits a value with no `__item_id` (which we treat as a brand-new item — the server fills it in).
- `__item_id` is stripped from any user-facing validation: `ConfigSpecs.get_and_check_values` is fed the dict minus `__item_id`. Item-id management is handled by the form-save service before validation.

Field paths used in `FormChangeEntry.field_path` (inside `FormSaveEvent.changes`):

- Top-level field: `mass`
- ParamSet item field: `samples[item_id=<uuid>].mass`
- Whole-item add/remove: `samples[item_id=<uuid>]` (a reorder is logged as remove + add of the same item_id)

This makes audit queries stable across UI reorderings.

---

## 8. Save & validation flow

```
POST /form/{id}/save  body = { name?, values, status_transition? }
```

1. Reject if form is not in `DRAFT` and the request is not a re-edit of a `SUBMITTED` form (re-edit is allowed; see §3.3).
2. Load `FormTemplateVersion.content` → `ConfigSpecs` (includes any `ComputedParam` entries).
3. Reconcile `__item_id`s in incoming ParamSet values (assign new ones for new items). Strip any client-submitted values for computed keys defensively.
4. **Type/range validation always runs** (per C10): each provided value is run through its `ParamSpec.validate(...)`. `ComputedParam` entries are skipped on the input pass (per §6.3). Missing mandatory values do NOT fail this step in `DRAFT`.
5. If the request includes `status_transition: "SUBMITTED"` → run full `ConfigSpecs.get_and_check_values(...)` to enforce all mandatory non-computed fields. Failure → 422 with the list of missing fields. Success → set `status=SUBMITTED`, `submitted_at`, `submitted_by`, and append a `STATUS_CHANGED` entry to the save event built in step 7.
6. Call `ConfigSpecs.compute_values(values, evaluator)` to produce the computed results, then merge them into the user values to form a single union dict. Per-computed-field errors are collected separately for the response (errors do not block save).
7. Diff old `values` vs the new union dict (user keys + computed keys) and build a single `FormSaveEvent` row whose `changes` list contains one entry per changed leaf path, one entry per ParamSet item add/remove, plus the `STATUS_CHANGED` entry from step 5 if any. A reorder of a ParamSet item produces a `PARAMSET_ITEM_REMOVED` entry followed by a `PARAMSET_ITEM_ADDED` entry for the same `__item_id` — there is no dedicated `MOVED` action. If `changes` is empty (no diff and no status transition), skip writing the row entirely. Computed-value changes ARE part of the diff and produce regular `FIELD_CREATED` / `FIELD_UPDATED` / `FIELD_DELETED` entries — useful for the audit trail.
8. Persist the union dict to `Form.values`. Return form + values + per-computed-field errors.

A separate `POST /form/{id}/submit` endpoint is sugar for "save + transition to SUBMITTED" in one call.

---

## 9. Routes

All routes live under `src/gws_core/form_template/form_template_controller.py` and `src/gws_core/form/form_controller.py`. Authentication required; no role checks (per G23).

### 9.1 FormTemplate routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/form-template` | Create template (auto-creates DRAFT v1). Body: `{name, description?, tags?}`. |
| `GET` | `/form-template/{id}` | Get template + version list summary. |
| `PUT` | `/form-template/{id}` | Update template-level fields (name, description, tags). |
| `DELETE` | `/form-template/{id}` | Hard delete. Rejected if any `Form` references any version (per G24). |
| `POST` | `/form-template/search` | Paginated search. Filters: name, tags, created_by, date range, is_archived. Builder extends `EntityWithTagSearchBuilder[FormTemplate]`. |
| `PUT` | `/form-template/{id}/archive` | Set `is_archived=true`. |
| `PUT` | `/form-template/{id}/unarchive` | Set `is_archived=false`. |
| `POST` | `/form-template/{id}/version` | Create a new DRAFT version. Rejected if a DRAFT already exists. Body may copy from latest published version. |
| `GET` | `/form-template/{id}/version/{version_id}` | Get one version (content + formulas). |
| `PUT` | `/form-template/{id}/version/{version_id}` | Update DRAFT version content/formulas. Rejected if not DRAFT. |
| `DELETE` | `/form-template/{id}/version/{version_id}` | Delete DRAFT (always) or ARCHIVED with no Form refs. |
| `POST` | `/form-template/{id}/version/{version_id}/publish` | DRAFT → PUBLISHED. Validates schema, assigns version number. |
| `POST` | `/form-template/{id}/version/{version_id}/archive` | PUBLISHED → ARCHIVED. |

### 9.2 Form routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/form` | Create. Body: `{template_version_id, name?, tags?}`. Version must be PUBLISHED. |
| `GET` | `/form/{id}` | Get form, schema, values, computed formulas, per-field errors. |
| `PUT` | `/form/{id}` | Update name/tags only. |
| `POST` | `/form/{id}/save` | Save values (see §8). Body: `{values, status_transition?}`. |
| `POST` | `/form/{id}/submit` | Sugar for save + SUBMITTED. |
| `DELETE` | `/form/{id}` | Hard delete. Cascade to FormSaveEvent. Application-layer guard: rejected if any Note references this form via a FORM block (frontend should detach references first). |
| `POST` | `/form/search` | Paginated search. Filters: name, tags, status, template_id, created_by, date range, is_archived. |
| `PUT` | `/form/{id}/archive` | Set `is_archived=true`. |
| `PUT` | `/form/{id}/unarchive` | Set `is_archived=false`. |
| `GET` | `/form/{id}/history` | Paginated save-event log (one item per save). Filters: user_id, date range. Each item returns the full `changes` list — clients filter by field path / action client-side, or via a dedicated query param that pushes a JSON-path filter into the DB once we add the GIN index. |

---

## 10. Services

- `FormTemplateService` — CRUD, version lifecycle, schema validation (delegates to `ConfigSpecs.check_config_specs()` which now includes cycle detection), archive guards, hard-delete usage check.
- `FormService` — create from version, save with diffing, submit, archive, history queries. Builds one `FormSaveEvent` per save with the diff list. Calls `ConfigSpecs.compute_values(...)` for read-only computed results.
- `ConfigSpecsEvaluator` (in `config/param/computed/`) — generic, not form-specific. Wraps `simpleeval` with the whitelisted function table and the `samples[].mass` aggregate sugar. Cycle detection lives in `ConfigSpecs.check_config_specs()`.
- `FormParamSetItemIdentityService` — assigns/preserves `__item_id`, computes the diff used to build the `FormSaveEvent.changes` list.

---

## 11. File layout

```
src/gws_core/
  form_template/
    __init__.py
    form_template.py                    # FormTemplate Peewee model
    form_template_version.py            # FormTemplateVersion Peewee model
    form_template_dto.py
    form_template_service.py
    form_template_controller.py
    form_template_search_builder.py
  form/
    __init__.py
    form.py                             # Form model
    form_save_event.py                  # FormSaveEvent model + FormChangeEntry DTO
    form_dto.py
    form_service.py
    form_search_builder.py
    form_controller.py
  config/param/computed/
    __init__.py
    computed_param.py                   # ComputedParam(ParamSpec) subclass
    computed_param_evaluator.py         # simpleeval-backed evaluator (generic)
  impl/rich_text/block/
    rich_text_block_form_template.py    # FORM_TEMPLATE block
    rich_text_block_form.py             # FORM block
  tag/
    tag_entity_type.py                  # add FORM_TEMPLATE, FORM enum entries
tests/test_gws_core/
  form_template/
    test_form_template_crud.py
    test_form_template_versioning.py
  form/
    test_form_crud.py
    test_form_save_and_submit.py
    test_form_save_events.py
    test_form_paramset_identity.py
  config/param/
    test_computed_param.py              # evaluator, scoping, errors, cycles
    test_computed_param_in_task.py      # ComputedParam declared in a Task
    test_config_specs_consumer_audit.py # mandatory_values_are_set, get_and_check_values, etc. skip computed
  impl/rich_text/
    test_form_blocks.py
    test_note_template_instantiation.py
docs/specs/
  form_feature.md                       # this file
```

---

## 12. DB migrations

A single migration adds:

- Table `gws_form_template` with FKs to user.
- Table `gws_form_template_version` with FK to `gws_form_template`, unique constraint `(template_id, version)`, and a partial unique constraint enforcing at most one `DRAFT` per template (`UNIQUE (template_id) WHERE status = 'DRAFT'`).
- Table `gws_form` with FK to `gws_form_template_version`.
- Table `gws_form_save_event` with FK to `gws_form` (cascade), JSON `changes` column, indexes `(form_id, created_at DESC)` and `(user_id, created_at DESC)`. No GIN index on `changes` in v1; add later if field-path filter queries become hot.
- Two new entries in the `TagEntityType` enum: `FORM_TEMPLATE`, `FORM` (no schema change — string column).
- One new entry in the `TagOriginType` enum: `FORM_TEMPLATE_PROPAGATED` (no schema change — string column).

Existing notes and note templates need no migration; the new block types are additive and old content keeps parsing.

---

## 13. Open questions / deferred decisions

1. **Native choice/date param specs.** Deferred (per A2). Until then, single-choice can be modeled as `StrParam` + UI-side allowed-values, multi-choice as `ListParam`, dates as `StrParam` with ISO format validation. We should decide on a v2 timeline before the form catalog grows large enough that backfilling becomes painful.
2. **Sections / display-only blocks inside the schema.** Deferred (per A1). Will require extending `ConfigSpecs` rather than the form layer.
3. **Conditional fields.** Deferred (per A3). Hook: a future `ParamSpec.visibility_condition` could be a formula expression evaluated at fill time.
4. **Public share URLs / anonymous filling.** Out of scope for v1 (per H26 follow-up).
5. **Upgrading existing Forms to a newer template version.** Out of scope (per B7).
6. **"Re-edit a SUBMITTED form" UX.** Allowed at the API level (per C9). UI may want a confirmation dialog; spec'd separately.
7. **Form value size cap.** No explicit cap. If forms grow large (file-upload-ish content via DictParam values), we may need to split the `values` JSON into a separate blob table — revisit when there's data.

---

## 14. Test plan (high level)

- `FormTemplate` CRUD + soft archive + hard-delete guard.
- Version lifecycle: create-template-creates-draft, publish-assigns-version, only-one-draft, publish-an-already-published-rejected, archive-published, draft-deletable, archived-deletable-only-without-refs.
- `Form` create rejects `DRAFT` and `ARCHIVED` template versions.
- Save in `DRAFT`: type validation runs, missing mandatories don't block.
- Submit: missing mandatories block with 422; success transitions and writes a `FormSaveEvent` whose `changes` list contains a `STATUS_CHANGED` entry.
- Re-edit a `SUBMITTED` form: status sticks, edits are logged in subsequent `FormSaveEvent` rows.
- `FormSaveEvent` shape: a save changing N fields produces exactly one row with N entries in `changes`; a no-op save (no diff, no transition) produces zero rows.
- ParamSet identity: add/edit/reorder/remove items across multiple saves; audit paths stay stable; reordering produces a `PARAMSET_ITEM_REMOVED` + `PARAMSET_ITEM_ADDED` pair for the same `__item_id` inside a single save event's `changes`.
- `ComputedParam`: each operator/function (including `concat` with scalars, with a list, and with a separator); missing field → null with error; division by zero → null with error; cycle → rejected by `check_config_specs()` at template publish AND at task class registration.
- `ComputedParam` per-row inside a `ParamSet` (e.g. `density = mass / volume`) and at outer scope (e.g. `total_mass = sum(samples[].mass)`).
- `ComputedParam` write defense: client-submitted value for a computed key is silently stripped; `validate(non_null)` raises.
- `ComputedParam` in a `Task`: declared in `config_specs`, recomputed by `task_runner` before `Task.run`, available in `params` like a normal key.
- Cross-cutting consumers (`mandatory_values_are_set`, `get_and_check_values`, `to_dto`, view runners, agents) all skip computed entries correctly.
- Rich text: insert `FORM_TEMPLATE` block in note template, instantiate to note → block becomes `FORM` with `is_owner=true` and a fresh form exists.
- Insert existing form into a second note (`is_owner=false`), edit from either note, both see the change.
- Note delete cascade: owner-only form deleted, owner+referenced form preserved.
- Search: filter by tag, status, template, date range; pagination.
- Tag propagation: propagable tag on `FormTemplate` reaches new `Form`s at creation; adding/removing a propagable tag on the template after the fact propagates to existing `Form`s; non-propagable tags don't copy; user-added tags on a `Form` survive removal of the template tag.
- Derived version lookups: "current draft" / "current published" queries return correct rows after publish/archive transitions; queries stay O(1) under EXPLAIN.

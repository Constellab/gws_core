# Phase 3 — `Form` CRUD + Save Flow

## Context

The form feature spec ([form_feature.md](bricks/gws_core/docs/form_feature.md)) is being implemented in phases per [form_implementation_plan.md](bricks/gws_core/docs/form_implementation_plan.md). Phase 0 (`ComputedParam`), Phase 1 (DB + skeleton models), and Phase 2 (`FormTemplate` CRUD + versioning) are merged.

What's in place when Phase 3 starts:

- `Form` Peewee model at [form.py](bricks/gws_core/src/gws_core/form/form.py) — fields, `count_for_template`, `count_for_version`, `to_dto`, `to_full_dto`. `@final`.
- `FormSaveEvent` Peewee model at [form_save_event.py](bricks/gws_core/src/gws_core/form/form_save_event.py) — FKs (cascade on form), `changes` JSON, `get_changes/set_changes`, `to_dto`. Indexes on `(form, created_at)` and `(user, created_at)`.
- DTOs at [form_dto.py](bricks/gws_core/src/gws_core/form/form_dto.py): `FormStatus`, `FormChangeAction`, `FormChangeEntry`, `FormDTO`, `FormFullDTO`, `FormSaveEventDTO`.
- `ActivityObjectType.FORM` already in [activity_dto.py](bricks/gws_core/src/gws_core/user/activity/activity_dto.py).
- `TagEntityType.FORM` and `TagOriginType.FORM_TEMPLATE_PROPAGATED` already registered (Phase 1).
- `ConfigSpecs.compute_values()`, `check_config_specs()`, `get_and_check_values()`, `mandatory_values_are_set()` all honour `accepts_user_input` (Phase 0 done).

Phase 3 makes a `Form` fillable. The deliverable is a self-contained, demo-able milestone: **"I can fill it"** — create a form from a published version, save partial values, submit when complete, browse the audit timeline.

---

## Scope (from spec §8, §9.2, §10)

1. `FormService` — create-from-version, save with diffing, submit, archive/unarchive, hard-delete with usage-guard stub, history queries.
2. `FormValuesService` — values-layer helper: assigns/preserves `__item_id` for ParamSet items, strips computed keys, runs spec validation, computes the diff feeding `FormSaveEvent.changes`.
3. `FormController` — all routes from spec §9.2.
4. `FormSearchBuilder` extending `EntityWithTagSearchBuilder[Form]`, with `status` and `template_id` custom filters.
5. New DTOs: `CreateFormDTO`, `UpdateFormDTO`, `SaveFormDTO`, `FormSaveResultDTO`.
6. Initial tag copy from `FormTemplate` to `Form` at creation time.
7. Tests under `tests/test_gws_core/form/` (directory does not yet exist — must include `__init__.py`).

**Out of scope:**

- Ongoing tag propagation when a template tag changes (Phase 4). Initial copy at create time IS in scope — see spec §3.5 and implementation plan line 61.
- `EntityNavigableModel` wiring for `Form ↔ FormTemplate` (Phase 4).
- Rich text `FORM` block (Phase 6) — the hard-delete-when-Note-references guard is a no-op stub.
- `NoteTemplate → Note` instantiation (Phase 7).

---

## Files to create

```
src/gws_core/form/
  form_service.py                         # NEW
  form_values_service.py                  # NEW
  form_controller.py                      # NEW
  form_search_builder.py                  # NEW
tests/test_gws_core/form/
  __init__.py                             # NEW (empty)
  test_form_crud.py                       # NEW
  test_form_save_and_submit.py            # NEW
  test_form_save_events.py                # NEW
  test_form_values_service.py          # NEW
```

## Files to edit

- [form_dto.py](bricks/gws_core/src/gws_core/form/form_dto.py) — add `CreateFormDTO`, `UpdateFormDTO`, `SaveFormDTO`, `FormSaveResultDTO`.

That's it. All other Phase 3 changes are additive new files.

---

## Reference patterns to copy

| Concern | Reference | Notes |
|---|---|---|
| Service shape, transactions, activity logging | [form_template_service.py](bricks/gws_core/src/gws_core/form_template/form_template_service.py) | `@GwsCoreDbManager.transaction()` on writes; `ActivityService.add(ActivityType.X, ActivityObjectType.FORM, id)`. |
| Archive/unarchive pattern | [form_template_service.py](bricks/gws_core/src/gws_core/form_template/form_template_service.py) | Guard against double-archive, log, delegate to `Model.archive(bool)`. |
| Hard-delete usage guard | [form_template_service.py](bricks/gws_core/src/gws_core/form_template/form_template_service.py) | Count FK refs, raise `BadRequestException`. |
| Controller route style | [form_template_controller.py](bricks/gws_core/src/gws_core/form_template/form_template_controller.py) | `@core_app.<verb>(...)`, `Depends(AuthorizationService.check_user_access_token)`, `.to_dto()` return. |
| Tag inheritance from parent | [note_service.py:497-502](bricks/gws_core/src/gws_core/note/note_service.py#L497-L502) | `EntityTagList.find_by_entity(...).build_tags_propagated(TagOriginType.X, parent_id)` then `.add_tags(...)`. |
| Search builder (custom filter) | [note_search_builder.py](bricks/gws_core/src/gws_core/note/note_search_builder.py) | `add_expression(Note.field.ilike(...))`. |
| Schema validation hook | [config_specs.py:117](bricks/gws_core/src/gws_core/config/config_specs.py#L117) | `ConfigSpecs.from_json(content).check_config_specs()` (Phase 0 already wired in `publish_version`). |
| Mandatory check on submit | [config_specs.py:170](bricks/gws_core/src/gws_core/config/config_specs.py#L170) | `get_and_check_values()` raises `MissingConfigsException`; `accepts_user_input=False` entries skipped automatically. |
| Compute on save & read | [config_specs.py:221](bricks/gws_core/src/gws_core/config/config_specs.py#L221) | Returns `(values_dict, errors_by_key)`. Errors are best-effort; do not block save. |
| Test base class | [base_test_case.py](bricks/gws_core/src/gws_core/test/base_test_case.py) | Extend `BaseTestCase`; call services directly; assert on models. |
| Phase 2 test layout | [test_form_template_versioning.py](bricks/gws_core/tests/test_gws_core/form_template/test_form_template_versioning.py) | One file per concern, state-machine coverage. |

---

## `FormService` — method list

State machine summary (per spec §3.3, §8):

```
[create from PUBLISHED version] ──► DRAFT ──[save]──► DRAFT
                                       │
                                       └──[submit | save status_transition=SUBMITTED]──► SUBMITTED
                                                              │
                                                              └──[save again]──► SUBMITTED   (re-edit, status sticks)

orthogonal: is_archived ─ archive / unarchive (any status)
hard delete: rejected if any Note references via FORM block (Phase 3 stub)
```

```python
class FormService:

    # ----- create / read -----
    @classmethod
    @GwsCoreDbManager.transaction()
    def create(cls, dto: CreateFormDTO) -> Form:
        """Create a Form from a PUBLISHED FormTemplateVersion. Reject DRAFT/ARCHIVED versions.
        Default name = template.name. Copy propagable tags from the parent template (initial copy)."""

    @classmethod
    def get_by_id_and_check(cls, form_id: str) -> Form: ...

    @classmethod
    def get_full(cls, form_id: str) -> FormSaveResultDTO:
        """Form + values + computed values + per-computed-field errors. Recomputes on read (spec §6.7)."""

    # ----- update / save -----
    @classmethod
    @GwsCoreDbManager.transaction()
    def update(cls, form_id: str, dto: UpdateFormDTO) -> Form:
        """Update name only. Tags via existing tag controller. Allowed in any status."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def save(cls, form_id: str, dto: SaveFormDTO) -> FormSaveResultDTO:
        """The spec §8 flow. See state-machine + invariants below.
        Returns form + new values + computed + errors.
        Writes at most one FormSaveEvent (none if no diff and no transition)."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def submit(cls, form_id: str) -> FormSaveResultDTO:
        """Sugar for save() with status_transition=SUBMITTED and no values change."""

    # ----- archive / delete -----
    @classmethod
    @GwsCoreDbManager.transaction()
    def archive(cls, form_id: str) -> Form: ...
    @classmethod
    @GwsCoreDbManager.transaction()
    def unarchive(cls, form_id: str) -> Form: ...

    @classmethod
    @GwsCoreDbManager.transaction()
    def hard_delete(cls, form_id: str) -> None:
        """Reject if any Note references this form via a FORM block.
        Phase 3: the check is a no-op stub (FORM blocks land in Phase 6).
        Cascade-deletes FormSaveEvent rows via the FK on_delete=CASCADE."""

    # ----- search / history -----
    @classmethod
    def search(cls, search: SearchParams, page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Form]: ...

    @classmethod
    def get_history(cls, form_id: str, search: SearchParams,
                    page: int = 0, number_of_items_per_page: int = 20
                    ) -> Paginator[FormSaveEvent]:
        """Paginated FormSaveEvent timeline for a form. Filters: user_id, date range.
        Order: created_at DESC (matches the (form, created_at) index)."""
```

### `save()` internal flow (spec §8 — eight steps)

The body of `save()` mirrors the spec line-by-line. Pseudocode:

```python
form = cls.get_by_id_and_check(form_id)

# 1. Status gate: DRAFT always OK. SUBMITTED is OK too (re-edit allowed, spec §3.3).
#    Archive does NOT block saves; that's a UI concern.

# 2. Load schema.
specs = ConfigSpecs.from_json(form.template_version.content or {})

# 3. Reconcile __item_id and defensively strip client-submitted computed-key values.
#    (Strip is on input only — computed values are stored alongside user values,
#    but we never trust the wire for computed keys; the evaluator owns them.)
new_values = FormValuesService.assign_item_ids(
    specs, dto.values, previous=form.values or {}
)
new_values = FormValuesService.strip_computed_keys(specs, new_values)

# 4. Always run type/range validation; missing mandatories don't fail in DRAFT.
#    ParamSet items are validated row-by-row with __item_id stripped before each call.
FormValuesService.validate_with_specs(specs, new_values)

# 5. Mandatory check on transition to SUBMITTED.
status_changed = False
if dto.status_transition == FormStatus.SUBMITTED and form.status != FormStatus.SUBMITTED:
    if not specs.mandatory_values_are_set(_strip_item_ids_recursively(new_values)):
        raise BadRequestException("Cannot submit: missing mandatory fields ...")  # 422 in controller
    form.status = FormStatus.SUBMITTED
    form.submitted_at = DateHelper.now_utc()
    form.submitted_by = CurrentUserService.get_and_check_current_user()
    status_changed = True

# 6. Compute derived values, then merge them into new_values (single union dict).
computed, errors = specs.compute_values(_strip_item_ids_recursively(new_values))
new_values = FormValuesService.merge_computed(specs, new_values, computed)

# 7. Diff full union (user keys + computed keys) and build the single FormSaveEvent row.
changes = FormValuesService.diff_values(form.values or {}, new_values)
if status_changed:
    changes.append(FormChangeEntry(
        field_path="__status", action=FormChangeAction.STATUS_CHANGED,
        old_value=FormStatus.DRAFT.value, new_value=FormStatus.SUBMITTED.value,
    ))

# 8. Persist union.
form.values = new_values
if dto.name is not None:
    form.name = dto.name
form.save()

# 8b. No-op suppression: skip the row entirely if no diff and no transition.
if changes:
    event = FormSaveEvent()
    event.form = form
    event.user = CurrentUserService.get_and_check_current_user()
    event.set_changes(changes)
    event.save()
    ActivityService.add(ActivityType.UPDATE, ActivityObjectType.FORM, form.id)

# 9. Return. errors travels alongside; per-field errors do not block save (spec §6.7).
return FormSaveResultDTO(form=form.to_full_dto(), errors=errors)
```

The controller maps `MissingConfigsException` → 422 (or wraps the `BadRequestException` with the missing list — match what `FormTemplateService.publish_version` does today).

---

## `FormValuesService` — method list

A values-layer helper sitting between the controller's raw input and the persisted/validated state. Four responsibilities, all stateless and DB-free so unit tests can drive them: assign ParamSet `__item_id`s, strip computed-key submissions, run spec validation, and diff old vs new values into `FormChangeEntry` rows. Spec §7 introduces `__item_id` as a reserved key; spec §3.4 defines the diff actions and `field_path` shape. This service is the subtle, TDD-friendly piece.

```python
class FormValuesService:

    ITEM_ID_KEY: ClassVar[str] = "__item_id"

    @classmethod
    def assign_item_ids(
        cls,
        specs: ConfigSpecs,
        incoming: dict[str, Any],
        previous: dict[str, Any],
    ) -> dict[str, Any]:
        """For every ParamSet entry in specs:
        - if an item dict has __item_id matching an item in `previous`, preserve it
        - if an item dict has __item_id not in `previous`, accept it as-is (client-provided new id is fine)
        - if an item dict has no __item_id, assign a fresh UUID v4
        Returns a deep-copied values dict with __item_id populated everywhere.
        Recurses into nested ParamSets."""

    @classmethod
    def strip_computed_keys(cls, specs: ConfigSpecs, values: dict[str, Any]) -> dict[str, Any]:
        """Drop keys whose spec.accepts_user_input is False. Recurse into ParamSet rows.
        Defensive input-side strip — clients must never write to computed keys; the
        evaluator owns those values. Used on the incoming dto.values, NOT on the
        stored values (computed values ARE stored — see merge_computed below)."""

    @classmethod
    def merge_computed(
        cls,
        specs: ConfigSpecs,
        user_values: dict[str, Any],
        computed: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge computed values into user_values, keyed by spec key. Recurses into
        ParamSet rows so per-row computed fields (e.g. density per sample) land on
        the right row. Returns the union dict that gets persisted to Form.values."""

    @classmethod
    def validate_with_specs(cls, specs: ConfigSpecs, values: dict[str, Any]) -> None:
        """Run type/range validation per ParamSpec.validate. ParamSet items are
        validated row-by-row with __item_id stripped before each call. Missing
        mandatories DO NOT raise here (DRAFT save allows partial)."""

    @classmethod
    def diff_values(
        cls,
        old: dict[str, Any],
        new: dict[str, Any],
        path_prefix: str = "",
    ) -> list[FormChangeEntry]:
        """Recursive diff producing FormChangeEntry list with field_path per spec §7:
          - top-level scalar → 'mass'
          - ParamSet item field → 'samples[item_id=<uuid>].mass'
          - whole item add/remove → 'samples[item_id=<uuid>]'
        Reorder = item removed + item added with the SAME __item_id (no MOVED action).
        Status changes are appended by the caller, not here."""
```

**Invariants tested in `test_form_values_service.py`:**

- `assign_item_ids` is idempotent on already-tagged input.
- A reorder of two ParamSet items produces one `PARAMSET_ITEM_REMOVED` + one `PARAMSET_ITEM_ADDED` for each item with stable `__item_id`s. Inner field changes that survive a reorder still surface as a single `FIELD_UPDATED` if values changed, or as nothing if values were preserved (the diff is value-based, not position-based).
- `diff_values` distinguishes `FIELD_CREATED` (key absent in `old`, present in `new`), `FIELD_UPDATED` (both sides present, value differs), `FIELD_DELETED` (present in `old`, absent in `new`).
- Stripping `__item_id` happens before any call to `ParamSpec.validate(...)` (otherwise list/dict validators flag the unknown key).

---

## Invariants enforced in the service layer

- **Source version must be PUBLISHED** at create time. DRAFT and ARCHIVED versions are rejected with `BadRequestException`.
- **`__item_id` is never user-validated.** It rides through the system as a reserved string but is never passed into `ParamSpec.validate(...)` nor `get_and_check_values(...)`.
- **Computed values are stored alongside user values in `Form.values`.** Recomputed on every save, then merged into the union dict that gets persisted. This keeps computed fields searchable through the same `EntityWithTagSearchBuilder` JSON-key filters that user fields use, and avoids a second column. Source of truth for queries is the persisted union; the spec's "recompute on read" property in §6.7 stays as a correctness invariant (assert stored == recomputed in dev/test).
- **Computed keys are stripped from incoming `dto.values`.** Defensive — clients must never write to computed keys; the evaluator owns those values. Strip is on the *input* side only; storage is the union.
- **No-op save writes nothing.** If `diff_values` is empty and no status transition occurs, no `FormSaveEvent` row is written and no `ActivityService` entry is logged.
- **One `FormSaveEvent` per save.** N field changes in one call → 1 row with N entries in `changes`.
- **Re-edit-after-SUBMITTED stays SUBMITTED.** Spec §3.3: "A SUBMITTED form can be re-edited (status stays SUBMITTED, but every edit is logged)." This is intentional and surprising — call it out in the PR description.
- **Submit gate uses `mandatory_values_are_set` over the post-`__item_id`-strip values.** Computed-input entries are skipped automatically by the Phase 0 changes ([config_specs.py:101](bricks/gws_core/src/gws_core/config/config_specs.py#L101)).
- **Hard-delete usage guard is a stub in Phase 3.** The function is wired but the body is a no-op (or `pass # TODO Phase 6: count FORM block references`). Cascade-delete of `FormSaveEvent` rows is handled by the FK `on_delete="CASCADE"` already declared in [form_save_event.py:17](bricks/gws_core/src/gws_core/form/form_save_event.py#L17).

---

## Activity logging

Use existing `ActivityType` enum entries (no new types needed):

| Action | `ActivityType` | `ActivityObjectType` | `object_id` |
|---|---|---|---|
| `FormService.create` | `CREATE` | `FORM` | `form.id` |
| `FormService.update` (name) | `UPDATE` | `FORM` | `form.id` |
| `FormService.save` (any non-empty change) | `UPDATE` | `FORM` | `form.id` |
| `FormService.submit` | `UPDATE` | `FORM` | `form.id` |
| `FormService.archive` | `ARCHIVE` | `FORM` | `form.id` |
| `FormService.unarchive` | `UNARCHIVE` | `FORM` | `form.id` |
| `FormService.hard_delete` | `DELETE` | `FORM` | `form.id` |

Submit shares `UPDATE` with save (no dedicated SUBMIT activity type — the `STATUS_CHANGED` entry in `FormSaveEvent.changes` captures the semantic transition). No-op saves don't log activity (consistent with not writing the event row).

---

## `FormController` — routes

Match spec §9.2. All routes use `Depends(AuthorizationService.check_user_access_token)`.

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| POST | `/form` | `CreateFormDTO` | `FormDTO` |
| GET | `/form/{id_}` | — | `FormSaveResultDTO` |
| PUT | `/form/{id_}` | `UpdateFormDTO` | `FormDTO` |
| POST | `/form/{id_}/save` | `SaveFormDTO` | `FormSaveResultDTO` |
| POST | `/form/{id_}/submit` | — | `FormSaveResultDTO` |
| DELETE | `/form/{id_}` | — | `None` |
| POST | `/form/search` | `SearchParams`, `page`, `number_of_items_per_page` | `PageDTO[FormDTO]` |
| PUT | `/form/{id_}/archive` | — | `FormDTO` |
| PUT | `/form/{id_}/unarchive` | — | `FormDTO` |
| GET | `/form/{id_}/history` | `SearchParams` (query), `page`, `number_of_items_per_page` | `PageDTO[FormSaveEventDTO]` |

OpenAPI tags: `"Form"`. Match the existing `form-template` summary phrasing.

---

## DTOs to add to `form_dto.py`

```python
class CreateFormDTO(BaseModelDTO):
    template_version_id: str
    name: str | None = None  # defaults to template.name when None

class UpdateFormDTO(BaseModelDTO):
    name: str | None = None
    # tags via existing tag controller; not modeled here

class SaveFormDTO(BaseModelDTO):
    values: dict[str, Any]
    name: str | None = None
    status_transition: FormStatus | None = None  # only SUBMITTED is meaningful in v1

class FormSaveResultDTO(BaseModelDTO):
    form: FormFullDTO   # form.values is the union (user keys + computed keys)
    errors: dict[str, str]   # per-computed-field error messages, keyed by spec key
```

---

## `FormSearchBuilder`

```python
class FormSearchBuilder(EntityWithTagSearchBuilder[Form]):
    def __init__(self) -> None:
        super().__init__(
            Form,
            TagEntityType.FORM,
            default_orders=[Form.last_modified_at.desc()],
        )

    def add_status_filter(self, status: FormStatus) -> None:
        self.add_expression(Form.status == status)

    def add_template_id_filter(self, template_id: str) -> None:
        self.add_expression(
            Form.template_version.in_(
                FormTemplateVersion.select(FormTemplateVersion.id)
                .where(FormTemplateVersion.template_id == template_id)
            )
        )
```

The base class already supports `name`, `tags`, `created_by`, `is_archived`, and date-range filters via `SearchParams` (matches spec §9.2). The two custom filters above cover `status` and `template_id`. Wire them in `search()` by reading the matching filter criteria from `SearchParams` and dispatching to the methods — match the pattern used in any existing search builder that has a custom filter.

---

## Test plan

Four test files, all extending `BaseTestCase`. Most tests drive the **service layer** directly. The three controller routes that have meaningful semantics beyond a thin pass-through (save, submit, history) get one HTTP smoke test each.

The implementation plan calls out (line 161): *"The ParamSet `__item_id` reconciliation and the diff-to-`changes` logic both have edge cases that are hard to spot in review. Write tests before the implementation for those two pieces specifically — they reward TDD."* Treat `test_form_values_service.py` as a TDD spike: red-green-refactor on the pure service before wiring `FormService.save`.

### `test_form_crud.py`

- create from a PUBLISHED version → returns form with `status=DRAFT`, `name=template.name`, `is_archived=False`, `values is None`.
- create with explicit `name` overrides default.
- create from a DRAFT version → rejected.
- create from an ARCHIVED version → rejected.
- create copies propagable tags from the parent `FormTemplate` to the new `Form` (see [note_service.py:497-502](bricks/gws_core/src/gws_core/note/note_service.py#L497-L502)). Non-propagable tags don't copy.
- update changes name; archive/unarchive flip `is_archived`; double-archive raises.
- hard delete cascades to `FormSaveEvent` rows (insert two events, delete form, expect zero events).
- hard-delete-with-Note-reference guard: stub today, but assert the function exists and currently allows delete (Phase 6 will flip the assertion).
- search by status, by template_id, by tag, by name; paginates.

### `test_form_save_and_submit.py`

The spec §8 flow end-to-end.

- save in DRAFT with partial values → succeeds; missing mandatories don't block; values persisted.
- save with `__item_id`-less ParamSet items → server assigns ids; subsequent save without changes is a no-op.
- save with type-invalid value → rejected.
- save submitting `status_transition=SUBMITTED` with all mandatories set → status becomes SUBMITTED, `submitted_at`/`submitted_by` set, `STATUS_CHANGED` entry appears in the save event's `changes`.
- save submitting `status_transition=SUBMITTED` with missing mandatories → 422 (or `BadRequestException` at service layer); status stays DRAFT.
- save again on a SUBMITTED form → status stays SUBMITTED, edits logged in a new `FormSaveEvent` (re-edit per spec §3.3).
- submit() sugar equals save with `status_transition=SUBMITTED` and no values change → produces a save event with only the STATUS_CHANGED entry.
- save persists computed values into `Form.values` alongside user keys (single union dict); response returns the form with `values` populated and `errors` for any failed computed-field evaluations (e.g. division by zero in a `ComputedParam`).
- get_full() returns the stored `Form.values` directly. In dev/test, also asserts `recompute(values) == stored computed entries` as a correctness invariant.
- search by a computed-field value works through the same JSON-key filter path as user fields (e.g. find forms where `total_mass > 100`).
- submit on an already-SUBMITTED form is a no-op (no second STATUS_CHANGED entry).

### `test_form_save_events.py`

- N-field save → 1 row with N entries.
- no-op save → 0 rows.
- `FIELD_CREATED` / `FIELD_UPDATED` / `FIELD_DELETED` actions emitted correctly.
- ParamSet item add → `PARAMSET_ITEM_ADDED`.
- ParamSet item remove → `PARAMSET_ITEM_REMOVED`.
- get_history() pagination: insert >page-size events, fetch by page, ordered `created_at DESC`.
- get_history() with `user_id` filter narrows correctly.
- get_history() with date-range filter narrows correctly.

### `test_form_values_service.py`

The TDD piece. Pure functions on `FormValuesService`.

- `assign_item_ids` adds `__item_id` UUIDs to fresh items.
- `assign_item_ids` preserves existing `__item_id`s.
- `assign_item_ids` is idempotent.
- `assign_item_ids` recurses into nested ParamSets.
- `strip_computed_keys` drops `accepts_user_input=False` keys at top level and inside ParamSet rows (input-side defensive strip).
- `merge_computed` writes computed values into the union dict at top level and into the matching ParamSet row by `__item_id`.
- `diff_values`: scalar create/update/delete.
- `diff_values`: ParamSet item add → single `PARAMSET_ITEM_ADDED` with `field_path = "samples[item_id=<uuid>]"`.
- `diff_values`: ParamSet item remove → single `PARAMSET_ITEM_REMOVED`.
- `diff_values`: ParamSet item field update emits `FIELD_UPDATED` with path `samples[item_id=<uuid>].mass`.
- `diff_values`: pure reorder → `REMOVED + ADDED` for each moved item with stable `__item_id`s; values preserved → no `FIELD_UPDATED` entries.
- `diff_values`: reorder + edit → `REMOVED + ADDED` + a `FIELD_UPDATED` for the edited field.

---

## Verification

1. `cd /lab/user/bricks/gws_core && gws server test test_form_crud && gws server test test_form_save_and_submit && gws server test test_form_save_events && gws server test test_form_paramset_identity`.
2. `gws server test all` — full suite to catch regressions in `FormTemplate`, tags, ConfigSpecs.
3. HTTP smoke flow against `gws server run`:
   - `POST /form-template {"name": "demo"}` → 200.
   - `PUT /form-template/{id}/version/{vid}` with a non-trivial spec including a `ComputedParam` (e.g. `density = mass / volume` inside a `samples` ParamSet, plus `total_mass = sum(samples[].mass)` outside).
   - `POST /form-template/{id}/version/{vid}/publish` → 200.
   - `POST /form` with `{template_version_id}` → 200, status=DRAFT.
   - `POST /form/{id}/save` with a couple of `samples` rows lacking `__item_id` → 200; the returned `form.values` is the union (user keys + `density` per row + outer `total_mass`); `__item_id`s appear on each ParamSet row.
   - `POST /form/{id}/save` again with no changes → 200; `GET /form/{id}/history` → 1 event (only the first save).
   - `POST /form/{id}/submit` → 200 if mandatories are filled; `GET /form/{id}/history` → 2 events; second event contains a `STATUS_CHANGED` entry.
   - `POST /form/{id}/save` with one field updated on the SUBMITTED form → 200; status still SUBMITTED; history grows by one.
   - `POST /form/search {"filtersCriteria": [{"key": "status", "value": "SUBMITTED"}]}` → returns the form.
   - `DELETE /form/{id}` → 200; `GET /form/{id}/history` returns 404.

---

## Notes / risk

- **Hard-delete-when-Note-references guard is a stub.** Phase 6 introduces the `FORM` rich text block; until then, no Note can reference a Form, so the guard's body is empty. Leave a `# TODO Phase 6` and a docstring pointing at spec §9.2 / §5.6 so the future PR knows where to wire the count query.
- **`ComputedParam` integration is in scope here, not deferred to Phase 5.** Phase 0 has landed (`compute_values`, `accepts_user_input`, cycle detection — see [config_specs.py:117-262](bricks/gws_core/src/gws_core/config/config_specs.py#L117-L262)), so calling `specs.compute_values(...)` from `save` and `get_full` is a one-liner and we should include it. The implementation plan's "Phase 5 = formulas in form save" is mostly already done by Phase 0; the residual Phase 5 work is form-specific test coverage and any defensive strip we might miss here. If Phase 0 had been less complete we could have stubbed it (`return ({}, {})`); given the actual state, including it is cheaper than stubbing and re-wiring.
- **Initial tag copy at create time IS in Phase 3** (per implementation plan line 61). Ongoing propagation when a template tag changes after the fact is **Phase 4** — that requires `Form` to implement `EntityNavigableModel` so the existing propagation walk reaches it. The implementation here calls `EntityTagList.find_by_entity(TagEntityType.FORM_TEMPLATE, template.id).build_tags_propagated(TagOriginType.FORM_TEMPLATE_PROPAGATED, template.id)` and adds the result to the new form's tag list, mirroring [note_service.py:497-502](bricks/gws_core/src/gws_core/note/note_service.py#L497-L502). Mark this clearly in the PR description so reviewers don't expect to see Phase 4 wiring.
- **Re-edit-after-SUBMITTED will surprise reviewers.** Spec §3.3: *"A `SUBMITTED` form can be re-edited (status stays `SUBMITTED`, but every edit is logged in `FormSaveEvent`). This matches the C9 decision: re-edit allowed, status sticks."* Cite this line in the PR description and in the docstring of `FormService.save`.
- **Biggest PR — split if review pressure is high.** The implementation plan (line 73) suggests **3a** (CRUD + simple save without ParamSet identity, scalar fields only) and **3b** (full `FormValuesService` — `__item_id` reconciliation, ParamSet diff, history, reorder semantics). The diff-and-identity piece is genuinely the riskiest and most reviewable in isolation; if 3a lands first it gives Phase 4/6 work an early Form to attach to.
- **`SaveFormDTO.values` typing is intentionally loose** (`dict[str, Any]`). ParamSet items contain `__item_id` plus arbitrary user-defined keys; we can't tighten this without leaking schema specifics into the wire format.
- **Cascade FK already in place.** `FormSaveEvent.form` has `on_delete="CASCADE"` ([form_save_event.py:17](bricks/gws_core/src/gws_core/form/form_save_event.py#L17)). No service-layer loop needed for the cascade — Peewee + the DB handle it.

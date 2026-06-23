# Phase 2 — `FormTemplate` CRUD + Versioning

## Context

The form feature spec ([form_feature.md](bricks/gws_core/docs/form_feature.md)) is being implemented in phases per [form_implementation_plan.md](bricks/gws_core/docs/form_implementation_plan.md). Phase 1 (DB + skeleton models) is already merged: `FormTemplate`, `FormTemplateVersion`, `Form`, `FormSaveEvent` Peewee models exist; tag enums (`TagEntityType.FORM_TEMPLATE`, `TagEntityType.FORM`, `TagOriginType.FORM_TEMPLATE_PROPAGATED`) are in place; DTOs `FormTemplateDTO`, `FormTemplateVersionDTO`, `FormTemplateFullDTO` are defined.

Phase 2 makes templates fully usable on their own: a user can create a template (which auto-creates a DRAFT v1), edit the draft schema, publish it (freezing content and assigning a version number), archive published versions, and search/tag templates. Form-filling is **not** part of Phase 2 — that's Phase 3.

The deliverable is a self-contained, demo-able milestone: "I can author a template via API." This plan stays inside `gws_core` and should not touch any other brick.

---

## Scope (from spec §9.1 and implementation plan Phase 2)

1. `FormTemplateService` — template-level CRUD, version-lifecycle methods, archive/unarchive, hard-delete with usage guard.
2. `FormTemplateController` — all routes from spec §9.1.
3. `FormTemplateSearchBuilder` extending `EntityWithTagSearchBuilder`.
4. Missing DTOs (`CreateFormTemplateDTO`, `UpdateFormTemplateDTO`, `CreateDraftVersionDTO`, `UpdateDraftVersionDTO`).
5. Add `FORM_TEMPLATE` to `ActivityObjectType` enum.
6. Tests: template CRUD + version lifecycle state-machine.

Out of scope: tag propagation behavior (Phase 4), form filling (Phase 3), `ComputedParam` schema validation hook (Phase 0/5 — keep `check_config_specs()` call as a TODO if Phase 0 hasn't merged yet).

---

## Files to create

```
src/gws_core/form_template/
  form_template_service.py            # NEW
  form_template_controller.py         # NEW
  form_template_search_builder.py     # NEW
tests/test_gws_core/form_template/
  __init__.py                         # NEW (empty)
  test_form_template_crud.py          # NEW
  test_form_template_versioning.py    # NEW
```

## Files to edit

- [form_template_dto.py](bricks/gws_core/src/gws_core/form_template/form_template_dto.py) — add `CreateFormTemplateDTO`, `UpdateFormTemplateDTO`, `CreateDraftVersionDTO`, `UpdateDraftVersionDTO`.
- [activity_dto.py](bricks/gws_core/src/gws_core/user/activity/activity_dto.py) — add `FORM_TEMPLATE = "FORM_TEMPLATE"` (and `FORM = "FORM"` while we're here, since Phase 3 will need it).
- [form_template.py](bricks/gws_core/src/gws_core/form_template/form_template.py) — add a `to_full_dto()` method that joins versions, mirroring the existing `to_dto()`.

---

## Reference patterns to copy

| Concern | Reference | Notes |
|---|---|---|
| Service shape (static methods, transactions) | [note_template_service.py](bricks/gws_core/src/gws_core/note_template/note_template_service.py) | `@GwsCoreDbManager.transaction()` on writes; `_create()` private helper; activity logging via `ActivityService.add()`. |
| Archive/unarchive pattern | [note_service.py:693-717](bricks/gws_core/src/gws_core/note/note_service.py#L693-L717) | Guard against double-archive, log activity, delegate to model `.archive(bool)`. The base `Model` class already provides `.archive()`. |
| Hard-delete usage guard | [resource_service.py:54-64](bricks/gws_core/src/gws_core/resource/resource_service.py#L54-L64) | Count FK references, raise `BadRequestException` if any. |
| Controller route style | [note_template_controller.py](bricks/gws_core/src/gws_core/note_template/note_template_controller.py) | `@core_app.<verb>(...)`, `Depends(AuthorizationService.check_user_access_token)`, return `.to_dto()`. |
| Search builder | [note_template_search_builder.py](bricks/gws_core/src/gws_core/note_template/note_template_search_builder.py) | One-line subclass passing model + `TagEntityType` + default ordering. |
| Tag attachment on entity create | [note_service.py:497-502](bricks/gws_core/src/gws_core/note/note_service.py#L497-L502) | `EntityTagList.find_by_entity(TagEntityType.X, id).add_tags(...)`. |
| Test base class | [base_test_case.py](bricks/gws_core/src/gws_core/test/base_test_case.py) | Extend `BaseTestCase`; call services directly; assert on models. |

---

## `FormTemplateService` — method list

State machine summary (per spec §3.2):

```
[create template] ──► DRAFT v=0 ──[publish]──► PUBLISHED v=N ──[archive]──► ARCHIVED
                          │                          (immutable)               │
                          └──[delete]                                          └──[hard-delete iff no Form refs]
```

```python
class FormTemplateService:

    # ----- template-level -----
    @classmethod
    @GwsCoreDbManager.transaction()
    def create(cls, dto: CreateFormTemplateDTO) -> FormTemplate:
        """Create FormTemplate + auto-create DRAFT v=0 with empty content. Attach tags."""

    @classmethod
    def get_by_id_and_check(cls, template_id: str) -> FormTemplate: ...

    @classmethod
    def get_full(cls, template_id: str) -> FormTemplateFullDTO:
        """Template + ordered list of versions (newest first)."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def update(cls, template_id: str, dto: UpdateFormTemplateDTO) -> FormTemplate:
        """Update name/description. Tags handled via existing tag controller."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def archive(cls, template_id: str) -> FormTemplate: ...     # mirrors note_service archive_note

    @classmethod
    @GwsCoreDbManager.transaction()
    def unarchive(cls, template_id: str) -> FormTemplate: ...

    @classmethod
    @GwsCoreDbManager.transaction()
    def hard_delete(cls, template_id: str) -> None:
        """Reject if any Form references any FormTemplateVersion of this template (per spec §4)."""

    # ----- search -----
    @classmethod
    def search(cls, search: SearchParams, page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[FormTemplate]: ...

    # ----- version-level -----
    @classmethod
    @GwsCoreDbManager.transaction()
    def create_draft(cls, template_id: str,
                     dto: CreateDraftVersionDTO | None = None) -> FormTemplateVersion:
        """Create new DRAFT. Reject if a DRAFT already exists for this template.
        If dto.copy_from_version_id is set and points at a PUBLISHED version, copy its content."""

    @classmethod
    def get_version(cls, template_id: str, version_id: str) -> FormTemplateVersion: ...

    @classmethod
    @GwsCoreDbManager.transaction()
    def update_draft(cls, template_id: str, version_id: str,
                     dto: UpdateDraftVersionDTO) -> FormTemplateVersion:
        """Update DRAFT content. Reject if status != DRAFT."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def publish_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        """DRAFT → PUBLISHED. Validates schema (ConfigSpecs.from_dto + check_config_specs),
        assigns version = max(version)+1 over PUBLISHED versions of this template,
        sets published_at / published_by."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def archive_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        """PUBLISHED → ARCHIVED. Reject otherwise."""

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_version(cls, template_id: str, version_id: str) -> None:
        """DRAFT: always deletable.
        ARCHIVED: deletable iff no Form references it.
        PUBLISHED: rejected — must be archived first."""
```

### Invariants enforced in the service layer

- **One DRAFT per template** — enforced both by the partial unique index from Phase 1 and by an explicit check in `create_draft()` so we get a clean error message rather than a DB integrity error.
- **Version number assignment** at publish: `max(version) WHERE status IN (PUBLISHED, ARCHIVED) + 1`. DRAFTs sit at `version=0` until publish (matches the model's existing default).
- **Schema validation at publish** — call `ConfigSpecs.from_dto(version.content).check_config_specs()`. If `ComputedParam`/Phase 0 hasn't landed yet, the existing `check_config_specs()` still validates the schema; cycle detection is a no-op in that case. Either way: if the call raises, refuse to publish and surface the error message.
- **Hard-delete usage guard for the template** — query: `Form.select().join(FormTemplateVersion).where(FormTemplateVersion.template_id == template_id).count() > 0` → `BadRequestException`. Use archive instead.
- **Hard-delete usage guard for an ARCHIVED version** — same query but scoped to a single `version_id`.

### Activity logging

Log `CREATE` / `UPDATE` / `DELETE` / `ARCHIVE` / `UNARCHIVE` activities with `object_type=ActivityObjectType.FORM_TEMPLATE`, `object_id=template_id`. Version-level operations also log against the parent template (the audit trail is at template granularity for now; finer granularity can come later if needed).

---

## `FormTemplateController` — routes

Match spec §9.1 exactly. All routes use `Depends(AuthorizationService.check_user_access_token)` for auth (no role checks per spec §G23).

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| POST | `/form-template` | `CreateFormTemplateDTO` | `FormTemplateDTO` |
| GET | `/form-template/{id_}` | — | `FormTemplateFullDTO` |
| PUT | `/form-template/{id_}` | `UpdateFormTemplateDTO` | `FormTemplateDTO` |
| DELETE | `/form-template/{id_}` | — | `None` |
| POST | `/form-template/search` | `SearchParams`, `page`, `number_of_items_per_page` | `PageDTO[FormTemplateDTO]` |
| PUT | `/form-template/{id_}/archive` | — | `FormTemplateDTO` |
| PUT | `/form-template/{id_}/unarchive` | — | `FormTemplateDTO` |
| POST | `/form-template/{id_}/version` | `CreateDraftVersionDTO` (optional `copy_from_version_id`) | `FormTemplateVersionDTO` |
| GET | `/form-template/{id_}/version/{version_id}` | — | `FormTemplateVersionDTO` |
| PUT | `/form-template/{id_}/version/{version_id}` | `UpdateDraftVersionDTO` (`content`) | `FormTemplateVersionDTO` |
| DELETE | `/form-template/{id_}/version/{version_id}` | — | `None` |
| POST | `/form-template/{id_}/version/{version_id}/publish` | — | `FormTemplateVersionDTO` |
| POST | `/form-template/{id_}/version/{version_id}/archive` | — | `FormTemplateVersionDTO` |

OpenAPI tags: `"Form template"`. Match the existing `note-template` summary phrasing.

---

## DTOs to add to `form_template_dto.py`

```python
class CreateFormTemplateDTO(BaseModelDTO):
    name: str
    description: str | None = None
    # Tag attachment: omitted for v1; clients call the existing tag controller after create.
    # If callers want one-shot create-with-tags, add a `tags: list[NewTagDTO] | None = None`
    # field later — keep the wire format aligned with how Note/NoteTemplate do it.

class UpdateFormTemplateDTO(BaseModelDTO):
    name: str | None = None
    description: str | None = None

class CreateDraftVersionDTO(BaseModelDTO):
    copy_from_version_id: str | None = None  # if set, copy that version's content

class UpdateDraftVersionDTO(BaseModelDTO):
    content: dict   # serialized ConfigSpecs (matches FormTemplateVersion.content)
```

---

## `FormTemplateSearchBuilder`

```python
class FormTemplateSearchBuilder(EntityWithTagSearchBuilder[FormTemplate]):
    def __init__(self) -> None:
        super().__init__(
            FormTemplate,
            TagEntityType.FORM_TEMPLATE,
            default_orders=[FormTemplate.last_modified_at.desc()],
        )
```

The base class already supports filter keys `name`, `tags`, `created_by`, `is_archived`, and date-range filters via `SearchParams`, matching the spec §9.1 filter list. No domain-specific filter is needed for v1.

---

## Test plan

Two test files, both extending `BaseTestCase` and exercising the **service layer** directly (the controller layer is thin enough that route-level tests would mostly retread service tests; we add one HTTP smoke test only if patterns elsewhere in the codebase do).

### `test_form_template_crud.py`

- create → returns template with name, description, `is_archived=False`, and exactly one DRAFT version (v=0).
- update name/description.
- archive → `is_archived=True`; double-archive raises.
- unarchive → `is_archived=False`; double-unarchive raises.
- hard delete with no forms succeeds; hard delete is unaffected by archive state.
- hard delete is rejected when at least one `Form` row references any of the template's versions (create a `Form` directly via the model to set up the precondition — Phase 3 service doesn't exist yet).
- search by name + by tag returns the template.

### `test_form_template_versioning.py`

State-machine coverage — this is where bugs hide:

- After `create()`, exactly one DRAFT exists with version=0.
- `create_draft()` rejected when a DRAFT already exists (clear error message).
- `create_draft(copy_from_version_id=...)` copies content from the referenced PUBLISHED version.
- `update_draft()` mutates content; rejected on PUBLISHED or ARCHIVED versions.
- `publish_version()`:
  - DRAFT → PUBLISHED, version goes from 0 to 1 (and to 2 on second publish, etc.).
  - Sets `published_at` and `published_by`.
  - Rejected if status != DRAFT.
  - Rejected if `ConfigSpecs.from_dto(content).check_config_specs()` raises (use a deliberately bad spec dict).
- After publish, the same template can have a new DRAFT created.
- `archive_version()` only on PUBLISHED.
- `delete_version()`:
  - DRAFT: succeeds.
  - PUBLISHED: rejected.
  - ARCHIVED with no `Form` refs: succeeds.
  - ARCHIVED with at least one `Form` ref: rejected.

---

## Verification

1. Type check: `cd /lab/user/bricks/gws_core && gws server test test_form_template_crud && gws server test test_form_template_versioning`.
2. Run the rest of the suite to catch regressions: `gws server test all`.
3. Manual smoke test against the running server:
   - `gws server run`
   - `POST /form-template` with `{"name": "demo"}` → 200, returns a template.
   - `GET /form-template/{id_}` → returns full DTO with one DRAFT version (v=0, status=DRAFT, content=`null` or `{}`).
   - `PUT /form-template/{id_}/version/{version_id}` with a minimal `ConfigSpecs.to_dto()` payload → 200.
   - `POST /form-template/{id_}/version/{version_id}/publish` → 200, status=PUBLISHED, version=1.
   - `POST /form-template/{id_}/version` (new draft) → 200, version=0, status=DRAFT.
   - `POST /form-template/search` with `{}` → returns the template in the page.

---

## Notes / risk

- **`ConfigSpecs.check_config_specs()` cycle detection is a Phase 0 deliverable.** If Phase 0 hasn't merged when this lands, calling `check_config_specs()` is still safe — it just won't catch `ComputedParam` cycles (which can't exist yet because `ComputedParam` doesn't exist yet). No special handling needed.
- **Tag attachment at create time** is intentionally deferred to a separate tag controller call (matches how Note/NoteTemplate work today). If reviewers push back, adding a `tags` field to `CreateFormTemplateDTO` is a one-line change.
- **DTO-vs-model symmetry:** `FormTemplateFullDTO.versions` should be ordered DRAFT first, then PUBLISHED versions newest-first, then ARCHIVED versions newest-first. Sorting on `version DESC` alone would push the DRAFT (`version=0`) to the bottom, which doesn't match how the UI wants to render the list. Implement as: `ORDER BY status_rank, version DESC` where `status_rank` is `0=DRAFT, 1=PUBLISHED, 2=ARCHIVED` (do this in Python after the query — clearer than a CASE expression).

# Phase 7 — NoteTemplate → Note Instantiation Hook + Cascade-on-Note-Delete + Join Models

## Context

The form feature spec ([form_feature.md](bricks/gws_core/docs/form_feature.md)) is being implemented in phases per [form_implementation_plan.md](bricks/gws_core/docs/form_implementation_plan.md). Phases 0 (`ComputedParam`), 1 (DB + skeleton models), 2 (`FormTemplate` CRUD + versioning), 3 (`Form` CRUD + save flow), 4 (tag propagation), 5 (computed params in form save), and 6 (rich text `FORM_TEMPLATE` / `FORM` blocks) are merged.

Phase 7 closes the note-side loop: instantiating a `NoteTemplate` containing `FORM_TEMPLATE` blocks transparently produces a `Note` with owned `FORM` blocks pointing at fresh `Form` rows; deleting that note cascades only to forms it actually owns. The deliverable is the spec §5.4 + §5.6 demo gate: **"Make a NoteTemplate with two `FORM_TEMPLATE` blocks, instantiate a Note, edit the forms, delete the Note, observe that owned forms vanish and referenced forms survive."**

**Phase 7 also lands the §3.6 join models** — `NoteFormModel` and `NoteTemplateFormTemplateModel` — so the cascade walk and the form/version hard-delete guards run as direct SQL queries instead of scanning rich-text JSON. This decision is documented in [form_feature.md §3.6](bricks/gws_core/docs/form_feature.md). The join models pattern follows [`NoteViewModel`](bricks/gws_core/src/gws_core/note/note_view_model.py) and its reconciliation hook [`_refresh_note_views_and_tags`](bricks/gws_core/src/gws_core/note/note_service.py#L724) verbatim.

What's in place when Phase 7 starts:

- `RichTextBlockTypeStandard.FORM_TEMPLATE` and `RichTextBlockTypeStandard.FORM` registered at [rich_text_block.py:28-29](bricks/gws_core/src/gws_core/impl/rich_text/block/rich_text_block.py#L28-L29).
- `RichTextBlockFormTemplate` payload (`form_template_id`, `form_template_version_id`, `display_name`) at [rich_text_block_form_template.py](bricks/gws_core/src/gws_core/impl/rich_text/block/rich_text_block_form_template.py).
- `RichTextBlockForm` payload (`form_id`, `is_owner`, `display_name`) at [rich_text_block_form.py](bricks/gws_core/src/gws_core/impl/rich_text/block/rich_text_block_form.py).
- `RichTextFormBlockValidator` enforcing context gating ([rich_text_form_validator.py](bricks/gws_core/src/gws_core/impl/rich_text/rich_text_form_validator.py)).
- `NoteService.insert_form_block_new` / `insert_form_block_reference` for §5.5 direct insertion ([note_service.py:258-298](bricks/gws_core/src/gws_core/note/note_service.py#L258-L298)).
- `NoteService.update_content` ([note_service.py:199](bricks/gws_core/src/gws_core/note/note_service.py#L199)) is the existing rich-text-mutation choke point that already calls `_refresh_note_views_and_tags(note)` at line 223. Phase 7 plugs in a sibling `_refresh_note_forms(note)` here — same shape as the views reconciliation.
- `NoteTemplateService.update_content` ([note_template_service.py:82](bricks/gws_core/src/gws_core/note_template/note_template_service.py#L82)) is the symmetric choke point for note templates; it has no reconciliation hook today and Phase 7 adds one.
- `NoteDeletedEvent` is dispatched **synchronously** before `note.delete_instance()` at [note_service.py:365](bricks/gws_core/src/gws_core/note/note_service.py#L365). Listeners register via `@event_listener` ([event_listener_decorator.py](bricks/gws_core/src/gws_core/model/event/event_listener_decorator.py)). With join models in place, the cascade listener no longer needs to inspect `event.content` — it queries `NoteFormModel.get_by_note(event.note_id)` directly *before* the deletion runs.
- `FormService.hard_delete` exists at [form_service.py:260-274](bricks/gws_core/src/gws_core/form/form_service.py#L260-L274) with a stale Phase 6 TODO; Phase 7 replaces it with a real guard backed by the new join.
- `FormService.create(CreateFormDTO)` accepts a `template_version_id`, validates `PUBLISHED`, copies propagated tags ([form_service.py:46-87](bricks/gws_core/src/gws_core/form/form_service.py#L46-L87)).
- `FormTemplateVersion.has_draft_for_template` exists; `get_current_published_version` does **not**. Phase 7 must add it (spec §3.1 lookup #2).
- Template-content copy on note instantiation happens at [note_service.py:74-81](bricks/gws_core/src/gws_core/note/note_service.py#L74-L81) — this is the seam where the conversion routine plugs in.
- The other Note-creation-from-template path is `insert_template` at [note_service.py:234-254](bricks/gws_core/src/gws_core/note/note_service.py#L234-L254) (insert a template's blocks into an *existing* note). Phase 7 must apply the same conversion here.

---

## Scope (from spec §3.6, §5.4, §5.6, §3.1 derived lookup)

1. **Two new join models** with composite primary keys, mirroring `NoteViewModel`:
   - `NoteFormModel(note FK CASCADE, form FK RESTRICT, is_owner bool)` — composite PK `(note, form)`.
   - `NoteTemplateFormTemplateModel(note_template FK CASCADE, form_template_version FK RESTRICT, form_template FK indexed)` — composite PK `(note_template, form_template_version)`. The denormalized `form_template` column lets queries skip the join through `FormTemplateVersion`.
2. **Event-driven reconciliation.** The form module owns two synchronous `@event_listener`s; the `note` / `note_template` modules just dispatch events. No imports of `form` from `note` / `note_template`.
   - `NoteContentUpdatedEvent` already exists ([note_events.py:16](bricks/gws_core/src/gws_core/note/note_events.py#L16), dispatched at [note_service.py:208](bricks/gws_core/src/gws_core/note/note_service.py#L208)). The form module subscribes a sync listener that reconciles `NoteFormModel` rows against the new content.
   - **New** `NoteTemplateContentUpdatedEvent` mirroring the Note event. Dispatched from `NoteTemplateService.update_content` ([note_template_service.py:82](bricks/gws_core/src/gws_core/note_template/note_template_service.py#L82)). The form module subscribes a sync listener for `NoteTemplateFormTemplateModel`.
   - **`NoteService.create` is currently a hole** — it writes `note.content = template.content` directly, bypassing both the validator and `update_content`. Phase 7 routes that path through the same dispatch (see step 3) so both validator and reconciliation get coverage.
3. **`FORM_TEMPLATE` → `FORM` conversion routine** at NoteTemplate→Note instantiation. Walk the template's content; for each `FORM_TEMPLATE` block, create a `Form` (status `DRAFT`, name = template.name) bound to the resolved version, replace the block with a `FORM` block carrying `form_id` and `is_owner=true`. The conversion is an **explicit transformation** owned by the form module — *not* a listener — to avoid relying on listener ordering relative to the reconciliation listener. Applied at:
   - `NoteService.create` — call the instantiator on the template content, then dispatch `NoteContentUpdatedEvent` so the validator and reconciliation listener run on the converted content.
   - `NoteService.insert_template` — call the instantiator on the template-block list before merging into the note, then route through `update_content` (which already dispatches the event).
4. **Archived-version fallback.** When the pinned `form_template_version_id` is `ARCHIVED`, fall back to the template's `current_published_version_id` (spec §3.1 derived lookup #2). If no published version exists, abort instantiation with a clear `BadRequestException`.
5. **Cascade on note delete** (§5.6). Sync listener on `NoteDeletedEvent`: query `NoteFormModel.get_by_note(event.note_id)` for owner rows; for each owner row, query whether *any other* `NoteFormModel` row references the same `form_id`; if none, delete the `Form`. Since `note` is `on_delete=CASCADE`, the join rows for the deleted note disappear automatically with the note — but the listener runs *before* `note.delete_instance()` (§5.6 requires the cascade decision to be made before the join rows vanish), so the query semantics are clean.
6. **Tighten `FormService.hard_delete` usage guard** (§5.6 dual). Reject hard-delete if `NoteFormModel.select().where(form == form_id)` has any rows. The DB-level `RESTRICT` FK is the belt; the application-level check is the braces (and produces a friendly error message naming up to 5 referencing notes). Replaces the stub TODO at [form_service.py:264-266](bricks/gws_core/src/gws_core/form/form_service.py#L264-L266).
7. **Tighten `FormTemplateService.hard_delete` (or `delete_archived_version`) usage guard.** Symmetric: reject if `NoteTemplateFormTemplateModel.select().where(form_template_version == version_id)` has any rows. Phase 2 already had a count-based guard against `Form` references; this is the new "and no note template still pins this version" leg.
8. **`FormTemplateVersion.get_current_published_version(template_id)`** — the helper backing the §3.1 derived lookup. Returns the latest `PUBLISHED` row or `None`.
9. **DB migration** creating the two join tables.
10. **One-shot backfill in the migration** (paranoid, ~5 lines): walk existing `Note` and `NoteTemplate` rows, parse content, insert join rows. Realistically this is a no-op in production (Phase 6 is the first version where blocks exist, and forms are not yet broadly used), but harmless on empty content and useful on dev/staging environments where developers have hand-built blocks.
11. Tests for instantiation, archived-fallback, cascade, owner-vs-non-owner, multi-note reference, the hard-delete guards, and join-table reconciliation.

**Out of scope:**

- Frontend instantiation UI flow (Phase 8).
- Adding new `FORM_TEMPLATE` block types or new payload fields. The block types are frozen by Phase 6.
- Conditional / template-side defaulting of form values. Spec §13 deferred.
- Re-pinning behavior when an already-instantiated form's underlying template version is archived. Spec §3.3 invariant: forms freeze at their version.

---

## Files to create

```
src/gws_core/note/
  note_form_model.py                           # NEW — NoteFormModel (mirrors note_view_model.py)
src/gws_core/note_template/
  note_template_form_template_model.py         # NEW — NoteTemplateFormTemplateModel
  note_template_form_instantiator.py           # NEW — §5.4 conversion routine
                                                #       (explicit transform, not a listener)
  note_template_events.py                      # NEW — NoteTemplateContentUpdatedEvent
src/gws_core/form/
  form_note_join_listener.py                   # NEW — sync listener on
                                                #       NoteContentUpdatedEvent: reconcile
                                                #       NoteFormModel
  form_note_template_join_listener.py          # NEW — sync listener on
                                                #       NoteTemplateContentUpdatedEvent:
                                                #       reconcile NoteTemplateFormTemplateModel
  form_note_cascade_listener.py                # NEW — sync NoteDeletedEvent listener
src/gws_core/core/db/migration/migrations/
  migration_<next>.py                          # NEW — create the two join tables + backfill
tests/test_gws_core/form/
  test_note_template_form_instantiation.py     # NEW — §5.4 conversion + archived fallback
  test_note_delete_form_cascade.py             # NEW — §5.6 cascade behavior
  test_form_hard_delete_guard.py               # NEW — note-references-form guard
  test_note_form_reconciliation.py             # NEW — join table sync via event
  test_note_template_form_template_reconciliation.py  # NEW — symmetric for templates
```

The form module owns three listeners (Note content, NoteTemplate content, Note delete) and the conversion routine. The `note` module gains nothing form-aware; the `note_template` module gains only its event class.

## Files to edit

- [note_service.py](bricks/gws_core/src/gws_core/note/note_service.py) —
  - `create()`: when `note_dto.template_id` is set, run `NoteTemplateFormInstantiator.instantiate(...)` to convert `FORM_TEMPLATE` blocks against the template content *before* assigning to `note.content`, then dispatch `NoteContentUpdatedEvent` (the same event already dispatched by `update_content`). This gives the create-from-template path validator coverage and join reconciliation for free, both of which it lacks today.
  - `insert_template()`: run the instantiator on the template's blocks before merging them into the note's rich text, then route through `update_content` (already does the dispatch).
  - **No** new `_refresh_note_forms` helper — the listener owns reconciliation.
- [note_template_service.py](bricks/gws_core/src/gws_core/note_template/note_template_service.py) —
  - `update_content()`: dispatch the new `NoteTemplateContentUpdatedEvent` synchronously before writing content (mirroring the Note event's contract).
  - **No** new reconciliation helper — the listener owns it.
- [form_service.py](bricks/gws_core/src/gws_core/form/form_service.py) — replace the stub TODO at line 264 with a guard backed by `NoteFormModel`.
- [form_template_service.py](bricks/gws_core/src/gws_core/form_template/form_template_service.py) — extend the existing version hard-delete guard with the `NoteTemplateFormTemplateModel` check.
- [form_template_version.py](bricks/gws_core/src/gws_core/form_template/form_template_version.py) — add `get_current_published_version`.
- [`__init__.py`](bricks/gws_core/src/gws_core/__init__.py) — re-export the join models and the new `NoteTemplateContentUpdatedEvent`; side-effect-import the three listener modules so their `@event_listener` registrations fire at package load.

No new DTOs, no new routes.

---

## Reference patterns to copy

| Concern | Reference | Notes |
|---|---|---|
| Composite-key join model with CASCADE/RESTRICT FKs | [note_view_model.py](bricks/gws_core/src/gws_core/note/note_view_model.py) | Verbatim shape. `force_insert=True` in `save()`, `Meta.primary_key = CompositeKey(...)`, `is_table = True`. |
| Diffing rich-text content against join rows | [note_service.py:724-784](bricks/gws_core/src/gws_core/note/note_service.py#L724-L784) | `_refresh_note_views_and_tags` is the canonical diff-and-reconcile shape: load existing rows, diff against parsed content, insert added, delete removed. The form listeners follow the same shape. The `is_owner` update on `NoteFormModel` is the small new wrinkle (views don't have a per-row mutable flag). |
| Sync listener on a Note event | [event_listener_decorator.py:34-42](bricks/gws_core/src/gws_core/model/event/event_listener_decorator.py#L34-L42) | `@event_listener` + `is_synchronous() -> True` so the listener runs in the caller's transaction and can roll it back on failure. |
| Existing event-class shape | [note_events.py](bricks/gws_core/src/gws_core/note/note_events.py) | `@dataclass`, `Literal["note"]` discriminator, `action` literal field. `NoteTemplateContentUpdatedEvent` follows the same template. |
| Walking rich-text blocks by type | [rich_text.py:88](bricks/gws_core/src/gws_core/impl/rich_text/rich_text.py#L88) | `rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM_TEMPLATE)` returns the typed list. |
| Building a `FORM` block | [note_service.py:315-321](bricks/gws_core/src/gws_core/note/note_service.py#L315-L321) | `RichTextBlock.from_data(RichTextBlockForm(form_id=..., is_owner=True, display_name=...))`. |
| Calling `FormService.create` | [note_service.py:268](bricks/gws_core/src/gws_core/note/note_service.py#L268) | `FormService.create(CreateFormDTO(template_version_id=...))`. |
| Resolving published version | [form_template_version.py:56-72](bricks/gws_core/src/gws_core/form_template/form_template_version.py#L56-L72) | `get_max_published_or_archived_version` is the closest; new helper mirrors it but filters `status == PUBLISHED` and returns the row. |
| Migration shape (table create + backfill) | [migration_0.py](bricks/gws_core/src/gws_core/core/db/migration/migrations/migration_0.py) | Recent migrations in this file show the create-table + data-shuffle pattern. |
| Hard-delete usage guard pattern | [form_template_service.py](bricks/gws_core/src/gws_core/form_template/form_template_service.py) | Phase 2/3 already follow this shape. |

---

## Cross-cutting concerns

### Listener semantics inside `update_content`

`NoteService.update_content` dispatches `NoteContentUpdatedEvent` *before* writing `note.content`, with `new_content` MUTABLE for sync listeners (per the existing docstring at [note_events.py:25](bricks/gws_core/src/gws_core/note/note_events.py#L25)). The form listener does **not** mutate `new_content` — its only job is to project the (post-validation) content into the join table. Concrete shape:

```python
@event_listener
class NoteFormJoinListener(EventListener):
    def is_synchronous(self) -> bool:
        return True

    def handle(self, event: Event) -> None:
        if not isinstance(event, NoteContentUpdatedEvent):
            return
        existing = {row.form_id: row for row in NoteFormModel.get_by_note(event.note_id)}
        target = _form_blocks_to_join_state(event.new_content)  # {form_id: is_owner}
        # diff: insert new, delete removed, update is_owner where it drifted
        ...
```

The diff happens in three buckets — inserted, removed, changed (`is_owner` flip). The listener runs in the caller's transaction; if it raises, the content update rolls back.

The existing `_refresh_note_views_and_tags` call inside `update_content` ([note_service.py:223](bricks/gws_core/src/gws_core/note/note_service.py#L223)) **stays where it is**. Phase 7 does not migrate it to a listener — that's a separate refactor. Phase 7 just *adds* a new listener for the form join.

### `NoteService.create` dispatches the event

This is the one place where `NoteService` itself changes for events. Today `create` writes `note.content = template.content` directly (no validator, no event dispatch — pre-existing inconsistency). Phase 7 routes the create-from-template path through the same dispatch the rest of the codebase already uses:

```python
if note_dto.template_id:
    template = NoteTemplate.get_by_id_and_check(note_dto.template_id)
    converted_content = NoteTemplateFormInstantiator.instantiate(template.content)
    # Existing dispatch contract — same one update_content uses.
    EventDispatcher.get_instance().dispatch(
        NoteContentUpdatedEvent(
            note_id=note.id,
            old_content=None,
            new_content=converted_content,
        )
    )
    # Validator runs as a sync listener? No — the validator is currently a
    # direct call inside update_content (line 204). Keep it a direct call
    # for create as well (call validate_for_note explicitly), so we don't
    # accidentally migrate validator semantics in this PR. Future cleanup
    # could turn the validator into a listener too.
    RichTextFormBlockValidator.validate_for_note(converted_content, None)
    note.content = converted_content
```

Listener ordering is therefore **not relevant** for Phase 7: the validator remains an explicit call, the conversion is an explicit call, and only the join-reconciliation listener subscribes to the event. One subscriber, no ordering questions.

### Why the conversion is not a listener

It's tempting to make the `FORM_TEMPLATE → FORM` conversion another sync listener that mutates `new_content`. Don't:

- The conversion has side effects (it creates `Form` rows). Listeners that create rows and mutate the event payload conflate two concerns.
- The conversion is needed only on NoteTemplate-instantiation paths, not on every `update_content`. Subscribing to every event and bailing out if no `FORM_TEMPLATE` blocks are present is wasted work *and* makes the contract murky ("this listener fires sometimes").
- Explicit conversion lets the caller surface a clear `BadRequestException` for the archived-with-no-published case (§5.4 step 1.1) without unwinding through the dispatcher.

Keep the conversion as a direct function call from `NoteService.create` and `NoteService.insert_template`.

### The cascade listener and the join

With the join in place, the cascade listener becomes:

```python
def handle(self, event: NoteDeletedEvent) -> None:
    if not isinstance(event, NoteDeletedEvent):
        return
    owner_rows = NoteFormModel.select().where(
        (NoteFormModel.note == event.note_id) & (NoteFormModel.is_owner == True)
    )
    for row in owner_rows:
        # Are there *other* notes still referencing this form?
        other_refs = NoteFormModel.select().where(
            (NoteFormModel.form == row.form_id) & (NoteFormModel.note != event.note_id)
        ).count()
        if other_refs == 0:
            # Safe to delete. Bypass FormService.hard_delete's join-guard
            # (the deleting note's join row still exists at this moment;
            # the guard would reject). Inline the teardown.
            form = Form.get_by_id(row.form_id)
            if form:
                form.delete_instance()
                ActivityService.add(
                    ActivityType.DELETE,
                    object_type=ActivityObjectType.FORM,
                    object_id=form.id,
                )
```

Notes:

- The listener runs *before* the note delete (per [note_service.py:365-372](bricks/gws_core/src/gws_core/note/note_service.py#L365-L372)). At this moment the deleting note's `NoteFormModel` rows still exist, which is why the "other refs" query needs the `note != event.note_id` filter.
- After the listener returns, `note.delete_instance()` runs, which (because `NoteFormModel.note` is `on_delete=CASCADE`) drops the join rows for the deleted note. Forms identified for deletion above were already removed; the FK `RESTRICT` from `Form` direction does not fire because no `NoteFormModel` row points at them anymore.
- If `Form.delete_instance()` fails (e.g. another `RESTRICT` FK), the surrounding transaction rolls back including the note delete. Desired behavior.

### Hard-delete guard message

`FormService.hard_delete`:

```python
def hard_delete(cls, form_id: str) -> None:
    referencing_notes = list(
        NoteFormModel.select().where(NoteFormModel.form == form_id)
    )
    if referencing_notes:
        names = ", ".join(r.note.title for r in referencing_notes[:5])
        suffix = f" (and {len(referencing_notes) - 5} more)" if len(referencing_notes) > 5 else ""
        raise BadRequestException(
            f"Cannot delete form: still referenced by note(s): {names}{suffix}. "
            f"Remove the form block from these notes first."
        )
    form = cls.get_by_id_and_check(form_id)
    form.delete_instance()
    ActivityService.add(...)
```

The DB-level `RESTRICT` FK catches the case where the application-level check is bypassed (e.g. raw SQL, future code path that forgets the guard). Layer-of-defense, not redundant.

### Backfill in the migration

Realistically a no-op in production today (Phase 6 just landed; very few `FORM_TEMPLATE` blocks exist anywhere yet). But cheap to write:

```python
for note in Note.select():
    rich_text = note.get_content_as_rich_text()
    for block in rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM):
        form_data = block.get_data()  # RichTextBlockForm
        NoteFormModel.get_or_create(
            note=note, form=form_data.form_id,
            defaults={"is_owner": form_data.is_owner},
        )
# Symmetric for NoteTemplate / FormTemplateVersion.
```

If a backfill row would violate the `RESTRICT` FK (e.g. a stale `form_id` in rich text pointing at a deleted form), log a warning and skip — the rich text was already broken, the migration shouldn't fail because of pre-existing inconsistency. Add an integration test that exercises this path with a deliberately stale block.

### Idempotency of the conversion routine

`NoteTemplate.content` cannot itself contain `FORM` blocks (the validator forbids it), so re-running the instantiator on a note that's already been instantiated is impossible: there are no `FORM_TEMPLATE` blocks left to convert. The routine is naturally idempotent on already-converted content (no-op). Mention this in the docstring.

### `is_owner` updates

Today, the only paths that flip `is_owner` are the §5.5 insertion routes (which insert a brand-new block — no flip happens, just a fresh row with the right value). The reconciliation must handle the case anyway: if a future API mutation flips `is_owner` on an existing block, the reconciliation diff updates the join row instead of insert-then-delete. Implementation: the diff runs in three buckets — inserted (new `(note, form)` not in DB), removed (DB row whose form no longer appears in content), changed (existing row whose `is_owner` value drifted from the block payload).

### Listener registration footgun

The `@event_listener` decorator self-registers at import time. **Three** new listeners must be imported during package init — `form_note_join_listener.py`, `form_note_template_join_listener.py`, `form_note_cascade_listener.py` — easiest is a side-effect import block in `gws_core/__init__.py` next to existing listener imports. Forgetting any of them means that listener silently doesn't fire; add a test per listener that dispatches a synthetic event and asserts the side effect (join row written, or form deleted). Pattern: `EventDispatcher.get_instance().get_registered_listeners()` ([event_dispatcher.py:200](bricks/gws_core/src/gws_core/model/event/event_dispatcher.py#L200)) returns the full set — assert by class name presence.

---

## Test plan

### `test_note_form_reconciliation.py` (new)

Goal: assert `NoteFormModel` stays in sync with rich-text content across all mutation paths.

```python
class TestNoteFormReconciliation(BaseTestCase):

    def test_insert_form_block_creates_join_row(self):
        # NoteService.insert_form_block_new → NoteFormModel row exists
        # with the right form_id and is_owner=True.

    def test_insert_reference_block_creates_join_row_with_is_owner_false(self):
        # NoteService.insert_form_block_reference → NoteFormModel row
        # is_owner=False.

    def test_remove_form_block_removes_join_row(self):
        # update_content with the FORM block stripped → row vanishes.

    def test_update_content_with_changed_is_owner_updates_join_row(self):
        # update_content where the FORM block's is_owner flips →
        # reconciliation updates the existing row, not insert+delete.

    def test_two_form_blocks_for_same_form_in_one_note_collapse_to_one_row(self):
        # Pathological but allowed: same form_id in two FORM blocks of
        # one note → exactly one NoteFormModel row.

    def test_create_note_from_template_populates_join_after_instantiation(self):
        # End-to-end: NoteTemplate with FORM_TEMPLATE → Note with FORM →
        # join row exists for the freshly-created form, is_owner=True.

    def test_cascade_on_note_delete_drops_join_rows(self):
        # FK on_delete=CASCADE: deleting a Note removes its
        # NoteFormModel rows automatically.

    def test_restrict_on_form_delete(self):
        # Manually try to delete_instance() on a Form referenced by a
        # NoteFormModel row → DB raises IntegrityError. Guard
        # belt-and-braces.

    def test_listener_is_registered_on_note_content_updated_event(self):
        # Belt-and-braces against the registration footgun: assert
        # NoteFormJoinListener appears in
        # EventDispatcher.get_instance().get_registered_listeners().

    def test_synthetic_dispatch_writes_join_row(self):
        # Bypass NoteService entirely: dispatch a synthetic
        # NoteContentUpdatedEvent with new_content carrying a FORM block
        # → NoteFormModel row appears. Confirms the wiring without
        # relying on update_content.
```

### `test_note_template_form_template_reconciliation.py` (new)

Symmetric coverage for `NoteTemplateFormTemplateModel`:

```python
class TestNoteTemplateFormTemplateReconciliation(BaseTestCase):

    def test_insert_form_template_block_creates_join_row(self):
        # NoteTemplateService.insert_form_template_block → row with
        # both form_template_version and form_template populated.

    def test_remove_form_template_block_removes_join_row(self):
        # update_content stripping the FORM_TEMPLATE block → row gone.

    def test_denormalized_form_template_matches_version(self):
        # Always equals form_template_version.template_id.

    def test_restrict_blocks_form_template_version_hard_delete(self):
        # Try to delete an ARCHIVED version still pinned by a
        # NoteTemplate → IntegrityError; FormTemplateService guard
        # catches it first with a friendly message.

    def test_cascade_on_note_template_delete_drops_join_rows(self):
        # Deleting a NoteTemplate drops join rows automatically.

    def test_listener_is_registered_on_note_template_content_updated_event(self):
        # Symmetric registration check.

    def test_update_content_dispatches_event_synchronously(self):
        # NoteTemplateService.update_content must dispatch
        # NoteTemplateContentUpdatedEvent. Subscribe a probe listener,
        # call update_content, assert the probe fired in the same call.
```

### `test_note_template_form_instantiation.py` (new)

Goal: assert spec §5.4 end-to-end through the `NoteService.create` path.

```python
class TestNoteTemplateFormInstantiation(BaseTestCase):

    # Happy path -------------------------------------------------------

    def test_create_note_from_template_with_one_form_template_block(self):
        # Build a NoteTemplate whose content has one FORM_TEMPLATE block
        # pinned to a PUBLISHED version. Create a Note from it. Assert:
        #   - The note's content has zero FORM_TEMPLATE blocks.
        #   - The note's content has exactly one FORM block.
        #   - The FORM block carries is_owner=True.
        #   - A new Form row exists, status=DRAFT, bound to that version.
        #   - The Form's name == template.name.
        #   - display_name on the new FORM block matches the source FORM_TEMPLATE.
        #   - NoteFormModel row exists, is_owner=True.

    def test_create_note_from_template_with_two_form_template_blocks(self):
        # Two FORM_TEMPLATE blocks → two distinct Forms, two FORM blocks,
        # two NoteFormModel rows, ordering preserved.

    def test_create_note_from_template_preserves_other_blocks(self):
        # Mix of paragraphs, headers, and one FORM_TEMPLATE.
        # Non-form blocks copy verbatim; only the FORM_TEMPLATE is rewritten.

    def test_insert_template_into_existing_note_also_converts(self):
        # NoteService.insert_template — same conversion semantics apply,
        # join rows added.

    # Archived-version fallback (spec §5.4 step 1.1) -------------------

    def test_archived_version_falls_back_to_current_published(self):
        # Template has v1 ARCHIVED, v2 PUBLISHED. NoteTemplate's
        # FORM_TEMPLATE block pins v1. Instantiation creates a Form
        # bound to v2. New FORM block points to that Form.

    def test_archived_with_no_published_aborts(self):
        # Template's only version is ARCHIVED. Instantiation raises
        # BadRequestException naming the template. Note NOT created.

    def test_dangling_template_id_aborts(self):
        # FORM_TEMPLATE block references a deleted FormTemplate.
        # BadRequestException, no partial note.

    # Idempotency / no-op ---------------------------------------------

    def test_template_with_no_form_template_blocks_is_unchanged(self):
        # NoteTemplate has only paragraphs. Resulting note's content
        # equals the template's content.

    # Validator interaction --------------------------------------------

    def test_resulting_note_passes_form_validator(self):
        # No FORM_TEMPLATE left, every FORM block resolves to a real Form.
```

### `test_note_delete_form_cascade.py` (new)

```python
class TestNoteDeleteFormCascade(BaseTestCase):

    def test_delete_note_deletes_owned_form(self):
        # Note with one FORM block, is_owner=True, no other notes
        # reference the form. Delete the note. Form is gone.

    def test_delete_note_cascades_form_save_events(self):
        # Owner form has FormSaveEvent rows. Note delete → both Form
        # and its events vanish (FK cascade).

    def test_delete_note_preserves_referenced_only_form(self):
        # Note has a FORM block with is_owner=False. Deleting this
        # note does NOT delete the form.

    def test_delete_note_preserves_owned_form_with_other_references(self):
        # Note A owns form F. Note B references F (is_owner=False).
        # Delete A. F survives.

    def test_delete_note_with_mixed_owner_and_reference_blocks(self):
        # One owner block, one reference block, both pointing at
        # different forms. After delete: owner-form gone, reference-form
        # survives.

    def test_form_delete_failure_rolls_back_note_delete(self):
        # Mock cascade path to raise. Note delete must roll back.

    def test_delete_note_without_form_blocks_is_unaffected(self):
        # Plain note deletes cleanly, no extraneous form-side activity.

    def test_cascade_listener_is_registered(self):
        # Belt-and-braces against the registration footgun: dispatch a
        # synthetic NoteDeletedEvent and assert handler was invoked.
```

### `test_form_hard_delete_guard.py` (new)

```python
class TestFormHardDeleteGuard(BaseTestCase):

    def test_hard_delete_rejected_when_owner_note_exists(self):
        # FormService.hard_delete raises BadRequestException naming
        # the note(s).

    def test_hard_delete_rejected_when_only_referenced_by_notes(self):
        # No owner, but a note references it. Still rejected.

    def test_hard_delete_succeeds_when_no_notes_reference_form(self):
        # No NoteFormModel rows → hard_delete succeeds.

    def test_db_restrict_fk_blocks_raw_form_delete(self):
        # Skip FormService entirely, call form.delete_instance() →
        # peewee raises IntegrityError. The DB layer catches the
        # bypass.

    def test_cascade_path_can_delete_form_even_with_zero_references(self):
        # The cascade-internal teardown works because by the time it
        # runs, only the deleting note's join row points at the form,
        # and we filter that out in the "other refs" query.
```

### Integration with existing suites

- No edits to `test_form_save_and_submit.py` or `test_form_template_versioning.py` for behavior changes. **Do** add one new test in `test_form_template_versioning.py` for the new "delete archived version rejected when note template still pins it" guard leg.
- A small check in `test_form_crud.py` (if it has a `test_hard_delete_*` block) to confirm the previously passing `hard_delete` test still passes — `NoteFormModel` is empty, so the new guard is a no-op there.

---

## Demo gate

After Phase 7:

1. `POST /note-template` (existing) → create a NoteTemplate, edit its content to insert two `FORM_TEMPLATE` blocks pointing at two PUBLISHED `FormTemplateVersion`s. `NoteTemplateFormTemplateModel` rows created.
2. `POST /note {"template_id": "..."}` → returns a Note whose content has two `FORM` blocks, `is_owner=true`, two new `Form` rows visible via `GET /form/search`, two `NoteFormModel` rows.
3. `POST /form/{id}/save` on each → values persist.
4. `POST /note/{other-id}/insert-form-block-reference {"form_id": <one of the above>}` → second note now references one of the forms, `is_owner=false`. New `NoteFormModel` row.
5. `DELETE /note/{first-note-id}` → the referenced form survives (other note still points at it), the unreferenced form is gone. `NoteFormModel` rows for the deleted note are gone (CASCADE).
6. `DELETE /form/{referenced-form-id}` → 422 with a message naming the second note. After the user removes the reference block from the second note (which removes the join row), `DELETE` succeeds.
7. Try to hard-delete the archived `FormTemplateVersion` while a different `NoteTemplate` still pins it → 422 naming the note template.

This exercises §3.6 (join models), §5.4 (instantiation), §5.6 (cascade), and both hard-delete guards, end to end.

---

## Verification

1. Targeted test runs:
   ```
   cd /lab/user/bricks/gws_core
   gws server test test_note_form_reconciliation
   gws server test test_note_template_form_template_reconciliation
   gws server test test_note_template_form_instantiation
   gws server test test_note_delete_form_cascade
   gws server test test_form_hard_delete_guard
   ```
2. Regression sweep on nearby suites: `test_form_crud`, `test_form_save_and_submit`, `test_form_template_versioning`, plus whichever existing note suite covers `update_content` (to confirm the new reconciliation hook doesn't regress views/tags).
3. HTTP smoke flow against `gws server run` per the demo-gate sequence above.
4. `gws server test all` only after the targeted runs are green.

---

## Notes / risk

- **The biggest risk is reconciliation drift.** With listeners, the audit shifts from "every content-mutation path calls the helper" to "every content-mutation path dispatches the event". `NoteService.update_content` already dispatches; Phase 7 adds dispatch to `NoteService.create` and `NoteTemplateService.update_content`. Audit: grep for `note.content =` and `document.content =` in both services and confirm every assignment that survives is reached via a path that dispatches. If a future PR adds another content-write path and forgets to dispatch, the join silently goes stale. The `RESTRICT` FK is the safety net (it catches drift at the next form/version delete attempt), but the better fix is making the dispatch unmissable — consider a follow-up to centralize content writes through a single private setter that always dispatches. Out of scope for Phase 7; flag it for review.
- **The `RESTRICT` FK is what makes this safe.** If reconciliation ever drifts (a join row exists but the form was deleted, or vice versa), the next FK-checked operation surfaces the bug loudly. Without `RESTRICT`, drift is silent.
- **Don't unify the two listener concerns into one handler.** The cascade listener does one thing (delete owned forms when their last note goes); a future "rebuild join" maintenance task is a separate command. Putting them in one place couples cold-path maintenance to the hot-path event handler.
- **The instantiator is the kind of code where a one-line bug deletes data.** Specifically: if the conversion accidentally drops a non-`FORM_TEMPLATE` block (`isinstance` check inverted), the new note silently loses content. Pair the happy-path test with `test_create_note_from_template_preserves_other_blocks` *before* writing the implementation — TDD this one.
- **The archived-fallback behavior is user-visible.** Surfacing "your note template referenced an archived version, we substituted v3" is a frontend concern (Phase 8). Backend just does the substitution; not flagged in any response field for v1.
- **The migration's backfill should NOT fail on pre-existing rich-text inconsistency.** If a stale `form_id` in rich text would violate `RESTRICT`, log a warning and skip. The rich text is already broken; the migration's job is to ship the schema, not to repair history. Add a dedicated test exercising this path.
- **`NoteFormModel.is_owner` is the only "queryable mirror of a block payload field" we're adding.** If a future change adds another mutable block-payload field that callers want to query, the reconciliation gains another diff bucket. Today there's only one — keep it that way.

---

## Sizing

| Item | Size |
|---|---|
| `note_form_model.py` | ~50 lines |
| `note_template_form_template_model.py` | ~60 lines |
| `note_template_events.py` (`NoteTemplateContentUpdatedEvent`) | ~20 lines |
| `note_template_form_instantiator.py` | ~80 lines |
| `form_note_join_listener.py` | ~70 lines |
| `form_note_template_join_listener.py` | ~70 lines |
| `form_note_cascade_listener.py` | ~40 lines |
| Migration (table create + backfill) | ~80 lines |
| `note_service.create` dispatch + instantiator wire-up | ~20 lines |
| `note_service.insert_template` instantiator wire-up | ~10 lines |
| `note_template_service.update_content` event dispatch | ~10 lines |
| `form_service.hard_delete` guard tightening | ~20 lines |
| `form_template_service.hard_delete` guard extension | ~10 lines |
| `form_template_version.get_current_published_version` | ~10 lines |
| Tests (five new files + edits) | ~600 lines combined |
| **Total** | **Medium (~4–5 days)** |

The implementation plan's original sizing line ("Phase 7 — Note instantiation hook — Small-medium — Conversion routine + cascade") underestimates by roughly 1–2 days because the join-model addition wasn't in the original spec. The trade — durable referential integrity backed by the DB — is worth the extra time. Update the sizing table in [form_implementation_plan.md](bricks/gws_core/docs/form_implementation_plan.md) accordingly when this lands.

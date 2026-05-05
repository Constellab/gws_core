# Form feature — future improvements

Short list of follow-ups that came up during Phase 7 implementation. Each one is small enough to land on its own when there's a reason to do it; none are blockers for shipping the feature today.

## 1. Orphaned forms (edit-time block removal)

### What happens today

When a user removes a `FORM` block from a note's content via `update_content`:

- The `NoteFormModel` join row is deleted (the listener reconciles correctly).
- **The `Form` row itself is NOT deleted**, even if the removed block was the only owner reference.

The §5.6 cascade fires only on `Note` hard-delete, not on edit-time block removal.

### Why we don't auto-delete on edit

Editor undo. If we deleted the Form when the owner block was removed, then the user pressing Ctrl+Z and re-saving would try to restore a block pointing at a `form_id` that no longer exists in the DB — the validator would reject the save and the user would lose both their form and the ability to undo. Every other rich-text editor (Notion, Confluence, Google Docs) follows the same rule: removing an embedded resource doesn't destroy the resource itself.

### Consequence

A `Form` whose owner block was removed via edit is "orphaned" — alive in the DB, with no `NoteFormModel` row pointing at it. It survives forever unless explicitly deleted via `FormService.hard_delete`.

### What to add (when we want to clean this up)

- **`FormService.find_orphaned()`** — returns forms with no `NoteFormModel` rows. Backs an "orphaned forms" cleanup view in the UI.
- **Editor "also delete the form?" prompt** — when the user removes a FORM block that's the only owner reference, surface a confirmation modal. Moves the destructive action out of the silent edit path so the user actively chooses.
- **Spec amendment** — add a sentence to §5.6 making the asymmetry explicit: "Note hard-delete cascades to owned forms; edit-time FORM-block removal does not. Removed forms become orphaned and survive until explicitly deleted, so editor undo can restore the reference."

### Alternatives considered

- **Soft-delete with TTL** — mark orphaned forms with `is_orphaned_at` timestamp, sweep after N days. Adds a new state, a sweeper job, and a TTL guess. Not worth it until orphans become a real volume problem.
- **Tombstone in note history** — let `Note.modifications` keep the form-block reference alive, never delete the Form. Pushes the cleanup problem to history pruning. Same end state as today.
- **Editor-driven restore** — on undo, the editor calls a "restore form from snapshot" endpoint to recreate the Form row. Lots of editor complexity, requires snapshotting form values, fails if you didn't snapshot.

## 2. Public-form URLs / anonymous filling

Out of scope for v1 (per spec §13). Audit log assumes `user_id NOT NULL`; that shape would change. Flag here so it's not forgotten.

## 3. Re-pinning forms to a newer template version

Out of scope for v1 (per spec §B7). Forms freeze at their version. If a use case appears, design needs to address: do values migrate? Does the form's status reset? What happens to ParamSet `__item_id` reconciliation across schema changes?

## 4. Conditional fields / visibility expressions

Spec §13 deferred. Hook would be `ParamSpec.visibility_condition` evaluated like a `ComputedParam` formula. No work needed today; flag for when the form catalog grows past the "every field is always visible" simplifying assumption.

## 5. Computed-field nested-key search

Phase 5 left `test_search_by_per_row_computed_value` as a TODO — the JSON-key filter path may not support nested keys today. Adding nested-key support to `EntityWithTagSearchBuilder` is a separate, larger change; only worth doing if a UI feature actually wants per-row search.

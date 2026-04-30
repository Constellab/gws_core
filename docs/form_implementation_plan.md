# Form Feature — Implementation Plan

Companion document to [`form_feature.md`](./form_feature.md). Splits the spec into mergeable phases ordered by dependency. Each phase leaves the system in a working state.

**General principle:** independent foundation first, form CRUD next, integrations last. One piece (`ComputedParam`) touches shared infrastructure that the form code depends on — it ships before the form module.

---

## Phase 0 — `ComputedParam` foundation

**Why first and why standalone:** it touches `ConfigSpecs`, the task runner, view runners, agents, and the streamlit UI. Keeping it in its own PR contains blast radius and lets the form feature ship later without coupling its review to a cross-cutting refactor. The form module imports a finished `ComputedParam`; if Phase 0 stalls, you can stub formulas with throwaway code in the form module to unblock the rest.

**Scope:**

1. Add `accepts_user_input` property to `ParamSpec` (default `True`).
2. Add `ComputedParam(ParamSpec)` + `ParamSpecType.COMPUTED` registration.
3. Add `ConfigSpecsEvaluator` (simpleeval wrapper, function whitelist, `samples[].field` aggregate sugar, `concat`).
4. Edit `ConfigSpecs`: `compute_values()`, cycle detection in `check_config_specs()`, skip-non-input behavior in `get_and_check_values()` / `mandatory_values_are_set()`, `accepts_user_input` flag in DTOs.
5. The §6.9 consumer audit — touch every grep'd call site, decide `skip` / `compute-then-include` / `reject`.
6. `task_runner` / `process_model` calls `compute_values` after input validation.
7. Tests: `test_computed_param.py`, `test_computed_param_in_task.py`, `test_config_specs_consumer_audit.py`.

**Validation gate:** every existing test still passes, plus a working task with a `ComputedParam` in its `config_specs`. This is the riskiest moment — green CI here means the form feature can layer on cleanly.

---

## Phase 1 — DB + skeleton models

Pure data layer, no behavior. Lets parallel work start on routes/UI without blocking on service logic.

**Scope:**

1. Migration: `gws_form_template`, `gws_form_template_version` (with partial unique on DRAFT and unique on `(template_id, version)`), `gws_form`, `gws_form_save_event` with the two indexes.
2. Peewee models for all four, no service methods yet, no DTOs beyond the obvious.
3. Add `TagEntityType.FORM_TEMPLATE`, `TagEntityType.FORM`, `TagOriginType.FORM_TEMPLATE_PROPAGATED`.
4. Smoke tests: rows insert, FKs cascade, partial unique constraint rejects two DRAFTs.

---

## Phase 2 — `FormTemplate` CRUD + versioning

Self-contained: a user can create a template, edit a draft, publish it, archive it. No form filling yet — but the template surface is fully usable.

**Scope:**

1. `FormTemplateService`: create (auto-creates DRAFT v1), update template-level fields, archive/unarchive, hard delete with usage guard.
2. Version lifecycle methods: create draft (rejects if one exists), update draft, publish (validates + assigns version + freezes), archive published, delete (draft always; archived only if unused).
3. `FormTemplateController` routes from spec §9.1.
4. `FormTemplateSearchBuilder` extending `EntityWithTagSearchBuilder`.
5. Tag attachment via existing `EntityTag` + `TagEntityType.FORM_TEMPLATE`. Propagation hook stub on the model (filled in Phase 4).
6. Tests covering version lifecycle exhaustively (this is the part with the most state-machine bugs).

---

## Phase 3 — `Form` CRUD + save flow

The core form-filling behavior. Depends on Phase 2 (needs published versions to bind to).

**Scope:**

1. `FormService.create_from_version` (rejects DRAFT/ARCHIVED versions, copies template tags via `EntityTagList.add_tags_and_propagate`).
2. `FormParamSetItemIdentityService` (the `__item_id` reconciliation logic — write this carefully, it's subtle).
3. `FormService.save`: spec §8 flow steps 1-7. Includes the diff-and-build-`changes` logic.
4. `FormSaveEvent` writes via the service, including the no-op-save suppression.
5. `FormService.submit` sugar.
6. Status transitions write the `STATUS_CHANGED` entry.
7. Re-edit-after-SUBMITTED behavior.
8. `FormController` routes from spec §9.2.
9. `FormSearchBuilder`.
10. `GET /form/{id}/history` returning paginated save events.
11. Tests: save flow, ParamSet identity stability across reorders, status transitions, re-edit, history pagination.

This is the biggest PR. If it's getting unwieldy, split into **3a** (CRUD + simple save) and **3b** (ParamSet identity + history).

---

## Phase 4 — Tag propagation `FormTemplate` → `Form`

Lands after Phase 3 because it needs a `Form` to propagate to.

**Scope:**

1. `Form` implements `EntityNavigableModel` exposing `FormTemplate` as upstream.
2. `FormTemplate` exposes downstream `Form`s for the propagation walk.
3. Wire it through whatever method `Note`/`Resource` use today (verify the actual call shape — the spec is illustrative on this point).
4. Tests: propagable tag on template reaches new forms; adding/removing a propagable tag on the template after the fact propagates to existing forms; non-propagable tags don't copy; user-added form tags survive removal of template tag.

---

## Phase 5 — `ComputedParam` integrated into form save

Depends on Phases 0 and 3. Hooks the evaluator into the form's read/save path.

**Scope:**

1. `FormService.save` calls `ConfigSpecs.compute_values(...)` after persistence and returns computed values + per-field errors in the response.
2. `GET /form/{id}` recomputes on read.
3. Defensive strip of client-submitted values for computed keys.
4. Tests: per-row formulas inside ParamSets, outer-scope aggregates, errors don't block save, cycle rejected at template publish.

If Phase 0 lands well, this phase is mostly wiring.

---

## Phase 6 — Rich text blocks `FORM_TEMPLATE` and `FORM`

Depends on Phase 3. Independent of Phases 4-5.

**Scope:**

1. `RichTextBlockTypeStandard` enum entries.
2. Two new block classes under `impl/rich_text/block/`.
3. Validation: `FORM_TEMPLATE` only valid in `NoteTemplate`, `FORM` only valid in `Note`.
4. Direct insertion paths: create-new-form-from-template, reference-existing-form (the spec §5.5 operations).
5. Tests for each block type's serialization, validation, and Note vs NoteTemplate gating.

---

## Phase 7 — NoteTemplate → Note instantiation hook

Depends on Phase 6. The conversion logic that swaps `FORM_TEMPLATE` blocks for owned `FORM` blocks.

**Scope:**

1. The conversion routine from spec §5.4: walk the template's blocks, for each `FORM_TEMPLATE` create a `Form` and emit a `FORM` block with `is_owner=true`.
2. Archived-version fallback to `current_published_version` (the derived lookup from spec §3.1), or abort with a clear error.
3. Cascade-on-note-delete logic from spec §5.6: delete owned forms only if no other note references them.
4. Tests: end-to-end "make a NoteTemplate with two form-template blocks, instantiate, edit forms, delete note, verify cascade".

---

## Phase 8 — Frontend (parallel to backend phases)

Frontend can start as soon as Phase 1 lands (it has the DTOs). Stub the API responses while the backend catches up.

Rough order:

1. FormTemplate editor (Phase 2 backend).
2. Form filler (Phase 3 backend).
3. Computed-field display (Phase 5 backend).
4. Rich text block renderers (Phase 6 backend).
5. NoteTemplate→Note instantiation UI flow (Phase 7 backend).

---

## Sequencing diagram

```
Phase 0 (ComputedParam)  ──┐
                            ├──► Phase 5 (formulas in form)
Phase 1 (DB) ──► Phase 2 ──┴──► Phase 3 ──┬──► Phase 4 (tag propagation)
                                          ├──► Phase 6 (rich text) ──► Phase 7 (note instantiation)
                                          └──► Phase 8 (frontend, parallel)
```

---

## Practical advice

- **Cut Phase 0 first and merge it before anything else.** It's the highest-risk piece because it touches shared code, and decoupling it from the form feature lets you debug shared-code regressions without form noise in the diff.
- **Phase 3 is where bugs hide.** The ParamSet `__item_id` reconciliation and the diff-to-`changes` logic both have edge cases that are hard to spot in review. Write tests *before* the implementation for those two pieces specifically — they reward TDD.
- **Phase 4 (propagation) and Phases 6-7 (rich text) are independent of each other.** If you have two people, run them in parallel after Phase 3.
- **Don't split Phase 2 into "template CRUD" and "version lifecycle".** The two are tightly coupled (creating a template auto-creates a draft) and splitting them adds throwaway temporary state.
- **Defer the public-form-URL question.** Out of scope for v1, and the audit log already has a `user_id NOT NULL` shape that would change if anonymous fills land — flag it now so reviewers don't bake the assumption deep.
- **Demo gates between phases.** After Phase 2: "I can author a template via API." After Phase 3: "I can fill it." After Phase 5: "Formulas compute." After Phase 7: "I can instantiate a note template and the embedded form just works." Each is a tight, demo-able milestone.

---

## Rough sizing

| Phase | Size | Notes |
|---|---|---|
| 0 — ComputedParam | Medium (~1 week) | Mostly the consumer audit. |
| 1 — DB skeleton | Small | Migration + models, no logic. |
| 2 — FormTemplate CRUD + versioning | Medium | Lifecycle state machine. |
| 3 — Form CRUD + save flow | **Large (~1.5–2 weeks)** | Biggest PR. Split into 3a/3b if it grows. |
| 4 — Tag propagation | Small-medium | Mostly wiring into existing system. |
| 5 — Formulas in form save | Small | If Phase 0 went well. |
| 6 — Rich text blocks | Medium | Two block types + Note/NoteTemplate gating. |
| 7 — Note instantiation hook | Small-medium | Conversion routine + cascade. |
| 8 — Frontend | Tracks alongside | Stub APIs as backend lands. |

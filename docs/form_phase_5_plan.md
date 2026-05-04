# Phase 5 — `ComputedParam` Integrated Into Form Save

## Context

The form feature spec ([form_feature.md](bricks/gws_core/docs/form_feature.md)) is being implemented in phases per [form_implementation_plan.md](bricks/gws_core/docs/form_implementation_plan.md). Phase 0 (`ComputedParam`), Phase 1 (DB + skeleton models), Phase 2 (`FormTemplate` CRUD + versioning), Phase 3 (`Form` CRUD + save flow), and Phase 4 (tag propagation) are merged.

**Phase 5 has no production code changes.** The Phase 3 plan made the explicit call (line 488) to fold `compute_values` integration into Phase 3 instead of deferring it: *"Phase 0 has landed (`compute_values`, `accepts_user_input`, cycle detection — see [config_specs.py:117-262](bricks/gws_core/src/gws_core/config/config_specs.py#L117-L262)), so calling `specs.compute_values(...)` from `save` and `get_full` is a one-liner and we should include it."* That call was made and the wiring shipped with Phase 3.

What's already in place:

- [form_service.py:171](bricks/gws_core/src/gws_core/form/form_service.py#L171) — `save()` calls `specs.compute_values(...)` after validation, propagates per-row computed cells back to id-bearing rows ([form_service.py:175](bricks/gws_core/src/gws_core/form/form_service.py#L175)), merges the outer-scope computed dict via `FormValuesService.merge_computed` ([form_service.py:176](bricks/gws_core/src/gws_core/form/form_service.py#L176)), and persists the union to `Form.values`.
- [form_service.py:105](bricks/gws_core/src/gws_core/form/form_service.py#L105) — `get_full()` recomputes against the stored values to surface fresh per-field errors.
- [form_values_service.py:86](bricks/gws_core/src/gws_core/form/form_values_service.py#L86) — `strip_computed_keys` runs the defensive input-side strip on `dto.values` (top-level + per-row).
- [form_template_service.py:231](bricks/gws_core/src/gws_core/form_template/form_template_service.py#L231) — `publish_version` already calls `check_config_specs()`, which delegates cycle detection to `ComputedParam.check_graph(...)`.
- Test coverage for the happy paths exists in [test_form_save_and_submit.py:167-224](bricks/gws_core/tests/test_gws_core/form/test_form_save_and_submit.py#L167-L224): per-row + outer-scope computation, division-by-zero non-blocking, `get_full` read, client-submitted-value strip.

**Phase 5 deliverable:** close the gaps that fall *between* Phase 0's evaluator-level coverage and Phase 3's happy-path coverage. These are real holes — the matrix below is what reviewers will ask about and what the spec §6.7 / §14 test plan calls out — but the implementation footprint is *test-only*.

---

## Scope

1. **Search by computed-field value** — verify the `EntityWithTagSearchBuilder` JSON-key filter path treats computed keys the same as user keys. This is currently *implicit* (storage is the union) but has no test, and the spec §14 line item explicitly calls it out: *"search by a computed-field value works through the same JSON-key filter path as user fields (e.g. find forms where total_mass > 100)."*
2. **Submit-time mandatory check excludes computed entries** — Phase 0's [config_specs.py:110](bricks/gws_core/src/gws_core/config/config_specs.py#L110) skip is in place, but there's no form-level test that proves a `ComputedParam` can never block submit (because `accepts_user_input=False`). One test covers the contract.
3. **Cycle rejection at template publish** — Phase 0 wires `check_config_specs()` into `publish_version`, but there is no test going through the form-template publish route with a cyclic `ComputedParam`. One test in `test_form_template_versioning.py` covers it.
4. **Per-field error key shape** — happy path is tested ([test_form_save_and_submit.py:188-199](bricks/gws_core/tests/test_gws_core/form/test_form_save_and_submit.py#L188)) but the matrix of error origins (missing field, type mismatch, empty aggregate, division by zero) at both per-row and outer scopes is not. The error key shape is what UIs key off, so test the contract: `samples[].density` for per-row, `total_mass` for outer.
5. **Computed-value diff in `FormSaveEvent.changes`** — spec §8 step 7 requires that *"Computed-value changes ARE part of the diff and produce regular `FIELD_CREATED` / `FIELD_UPDATED` / `FIELD_DELETED` entries — useful for the audit trail."* The diff logic in [form_values_service.py:208](bricks/gws_core/src/gws_core/form/form_values_service.py#L208) is value-based and already does this, but no test asserts it. One test pins the contract.
6. **Re-edit on SUBMITTED still recomputes** — spec §3.3 + §6.7 interaction: a re-edit on a SUBMITTED form must update computed cells in storage. Phase 3 has `test_re_edit_after_submitted_keeps_status` ([test_form_save_and_submit.py:136](bricks/gws_core/tests/test_gws_core/form/test_form_save_and_submit.py#L136)) but it doesn't exercise computed values. One test covers the regression.

**Out of scope:**

- Any production code changes. The save path (which maintains the recompute-on-read invariant) is already correct and tested in Phase 3; Phase 5 does not touch it.
- New evaluator features. The expression language (§6.4) is finalized in Phase 0.
- New `ParamSpec` types. Spec §2 non-goal.
- Conditional fields / visibility expressions. Spec §13 deferred.
- Streamlit live-recompute UI. Spec §6.8 — frontend work, tracked under Phase 8.
- `Task`-side computed-param wiring. Already covered by Phase 0 ([test_computed_param.py:420](bricks/gws_core/tests/test_gws_core/config/test_computed_param.py#L420), `TestComputedParamInTask`).

---

## Files to create

```
tests/test_gws_core/form/
  test_form_computed_values.py          # NEW — single home for Phase 5 coverage
```

Co-locating Phase 5's residual coverage in one new file (rather than scattering across `test_form_save_and_submit.py` / `test_form_template_versioning.py` / `test_form_save_events.py`) makes the PR diff small and the demo gate ("formulas compute, end to end") legible. Cross-cutting tests that don't fit neatly in one bucket — search-by-computed, error-key-shape matrix, computed-in-diff, re-edit recompute — share this file.

The two exceptions live in their natural homes:

- **Cycle rejection at template publish** belongs in `test_form_template_versioning.py` (it's a publish-route test, not a form-fill test).
- **Submit gate excludes computed** can sit in `test_form_save_and_submit.py` next to the existing submit tests (it's a submit-flow contract).

## Files to edit

- [test_form_template_versioning.py](bricks/gws_core/tests/test_gws_core/form_template/test_form_template_versioning.py) — add the publish-rejects-cyclic-spec test.
- [test_form_save_and_submit.py](bricks/gws_core/tests/test_gws_core/form/test_form_save_and_submit.py) — add the submit-gate-excludes-computed test.

That's it. No production module changes, no new DTOs, no new routes.

---

## Test plan — the matrix that closes the gap

### `test_form_computed_values.py` (new)

```python
class TestFormComputedValues(BaseTestCase):

    # Search by computed-field value (spec §14) -------------------------

    def test_search_by_outer_computed_field_value(self):
        # Three forms with total_mass = 1.0, 50.0, 200.0.
        # Search filter on total_mass > 100 returns one form.
        # Confirms storage-is-union → JSON-key search "just works".

    def test_search_by_per_row_computed_value(self):
        # Less critical (per-row search isn't a UI feature today) — but if
        # the JSON-key filter supports nested paths, document the behavior.
        # Skip with a TODO if the search infra doesn't support nested keys.

    # Per-field error key shape matrix (spec §6.7 / §14) ----------------

    def test_error_key_for_per_row_division_by_zero(self):
        # Already covered indirectly in test_form_save_and_submit.py:188.
        # Re-pin the contract here next to its siblings.

    def test_error_key_for_outer_scope_field(self):
        # Outer formula references a missing user field → errors["total_mass"].

    def test_error_key_for_per_row_missing_field(self):
        # Per-row formula references a missing sibling → errors["samples[].<key>"].

    def test_error_key_for_outer_aggregate_over_empty_paramset(self):
        # sum(samples[].mass) when samples is [] → errors["total_mass"].

    def test_error_key_for_type_mismatch(self):
        # User field is StrParam but referenced in arithmetic → error surfaces.

    # Computed values in the audit diff (spec §8 step 7) ----------------

    def test_computed_value_change_appears_in_save_event_changes(self):
        # Save with mass=1.0 → density=2.0 written.
        # Save with mass=2.0 → second event's `changes` includes a
        # FIELD_UPDATED entry for samples[item_id=...].density (old=2.0, new=4.0).

    def test_computed_value_creation_appears_as_field_created(self):
        # First save populates total_mass for the first time → FIELD_CREATED
        # entry for total_mass with old=None, new=<computed>.

    # Re-edit on SUBMITTED still recomputes (regression guard) ----------

    def test_re_edit_on_submitted_recomputes_computed_values(self):
        # Already-submitted form, re-edit a user field → computed values
        # update in storage and in the response. (Spec §3.3 + §6.7
        # interaction; not currently tested.)
```

Helper: `_computed_form()` mirrors the helper of the same name in `test_form_save_and_submit.py`. Lift it to a small shared fixture if both files start to use it; otherwise duplicate three lines.

### `test_form_template_versioning.py` (edit)

```python
def test_publish_rejects_cyclic_computed_param(self):
    template = FormTemplateService.create(CreateFormTemplateDTO(name="t"))
    draft = next(v for v in template.versions if v.status == FormTemplateVersionStatus.DRAFT)
    cyclic = ConfigSpecs({
        "a": ComputedParam(expression="b + 1", result_type="float"),
        "b": ComputedParam(expression="a + 1", result_type="float"),
    })
    FormTemplateService.update_draft(
        template.id, draft.id,
        UpdateDraftVersionDTO(content=_serialize(cyclic)),
    )
    with self.assertRaises(BadRequestException):
        FormTemplateService.publish_version(template.id, draft.id)
```

Phase 0 has unit-level cycle tests ([test_computed_param.py:322](bricks/gws_core/tests/test_gws_core/config/test_computed_param.py#L322), `test_cycle_detected_at_check_config_specs`); this is the integration test for the form-template publish route specifically.

### `test_form_save_and_submit.py` (edit)

```python
def test_submit_gate_does_not_block_on_unset_computed_param(self):
    # Build a template with a mandatory user field + a ComputedParam.
    # Save user field. Submit. Submit succeeds — ComputedParam was never
    # required and never blocked the gate, even before computation runs.
    # (Belt-and-braces around config_specs.py:110 + .py:191.)
```

---

## Verification

1. `cd /lab/user/bricks/gws_core && gws server test test_form_computed_values && gws server test test_form_save_and_submit && gws server test test_form_template_versioning`.
2. `gws server test all` — full regression sweep, with focus on `test_computed_param.py`, the form suite, and the form-template suite.
3. HTTP smoke flow against `gws server run`:
   - `POST /form-template {"name":"demo"}` → 200.
   - `PUT /form-template/{id}/version/{vid}` with `samples` ParamSet (`mass`, `volume`, `density = mass/volume`) + outer `total_mass = sum(samples[].mass)`.
   - `POST /form-template/{id}/version/{vid}/publish` → 200.
   - `POST /form` from that version → 200.
   - `POST /form/{id}/save` with two `samples` rows → returned `form.values` carries `density` per row and `total_mass` outer; `errors` empty.
   - `POST /form/{id}/save` with `volume=0` on one row → `errors` has `samples[].density`; the row's `density` is `None`; save still succeeded.
   - `GET /form/{id}` → values match what was stored.
   - `POST /form/search {"filtersCriteria":[{"key":"total_mass","operator":">","value":1.0}]}` (verify the `EntityWithTagSearchBuilder` filter syntax — `note_search_builder.py` is the closest reference) → returns the form.
   - Cyclic publish: `PUT` a draft with `a = b + 1, b = a + 1`; `POST .../publish` → 422 with the cycle error message.

---

## Notes / risk

- **The biggest risk is over-engineering.** Phase 0 + Phase 3 took the obvious shortcut (fold `compute_values` integration into Phase 3) and it paid off. Phase 5 should *not* re-justify any of that; the Phase 5 PR description should explicitly say *"Phase 0 and Phase 3 already wire computation into the form save/read path. This PR closes the residual test-matrix only — no production code changes."* If it grows beyond ~300 lines of test code, push back on scope.
- **Spec §6.7's "assert stored == recompute(values) in dev/test" line is intentionally not implemented.** The save path is what maintains the invariant, and the save path is already covered by Phase 3 tests ([test_form_save_and_submit.py:167-209](bricks/gws_core/tests/test_gws_core/form/test_form_save_and_submit.py#L167-L209)). Adding a runtime check inside `get_full` (which is on the hot UI read path — `GET /form/{id}` is called every time a user opens a form) would either (a) trade hot-path cost for redundant safety, or (b) require dev/prod branching, which is the wrong shape for the codebase. If a future bug causes drift, the existing save tests catch it; if they don't, the right fix is more save tests, not a read-side check.
- **Per-row search** is the one matrix cell where the test plan has a genuine TODO. The JSON-key filter path may not support nested keys today; if it doesn't, leave the test skipped with a comment pointing at the search builder. Adding nested-key support is a separate, larger change and is **out of scope for Phase 5**.
- **No new test data fixture is needed.** All scenarios reuse the `_computed_form()` factory pattern from `test_form_save_and_submit.py`. Lift it to a tiny shared module under `tests/test_gws_core/form/_computed_fixtures.py` *only if* both files start importing it; otherwise duplicate (three lines).
- **Demo gate.** After Phase 5: *"Formulas compute, the audit log records computed-value changes, and the test matrix matches the spec."* This is the smallest and shortest-feedback-loop phase of the form feature; expect it to land in a day.

---

## Sizing

| Item | Size |
|---|---|
| `test_form_computed_values.py` | ~250 lines |
| Two edits to existing test files | ~40 lines combined |
| Production code changes | none |
| **Total** | **Small (~1 day)** |

Per the implementation plan's own sizing line ("Phase 5 — Formulas in form save — Small — If Phase 0 went well"), this matches the original estimate. With no production code changes, it's even smaller than the original sizing assumed.

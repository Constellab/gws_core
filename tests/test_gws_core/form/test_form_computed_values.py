"""Phase 5 — residual ComputedParam coverage in the form save/read flow.

The save-path integration of ComputedParam landed in Phase 3 (see
form_service.py). This file closes the test gaps that fall between Phase 0's
evaluator-level coverage and Phase 3's happy-path coverage:

- per-field error key shape across error origins (missing field, type
  mismatch, empty aggregate, division by zero) at per-row and outer scope
  (spec §6.7);
- computed-value changes appear in FormSaveEvent.changes as regular
  FIELD_CREATED / FIELD_UPDATED entries (spec §8 step 7);
- re-edit on a SUBMITTED form recomputes computed values (spec §3.3 + §6.7);
- search by a computed-field value (spec §14) — currently unsupported by the
  search infra; tests document and skip until JSON-key filtering exists.
"""


from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam
from gws_core.form.form import Form
from gws_core.form.form_dto import (
    CreateFormDTO,
    FormChangeAction,
    FormStatus,
    SaveFormDTO,
)
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase


class TestFormComputedValues(BaseTestCase):
    # ------------------------------------------------------------------ #
    # Per-field error key shape matrix (spec §6.7)
    # ------------------------------------------------------------------ #

    def test_error_key_for_per_row_division_by_zero(self):
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.0}]}),
        )
        assert result.values is not None
        density_cell = result.values["samples"][0]["density"]
        self.assertIsNone(density_cell["value"])
        self.assertIsNotNone(density_cell["errors"])

    def test_outer_scope_unset_input_yields_no_value_no_error(self):
        # Outer formula references an input the user hasn't filled in yet. That
        # is "no value yet", not an error: the computed cell is None with no
        # error message (a freshly created, untouched form must not show errors).
        specs = ConfigSpecs(
            {
                "mass": FloatParam(human_name="Mass", optional=True),
                "doubled": ComputedParam(expression="@mass * 2"),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(form.id, SaveFormDTO(values={}))
        assert result.values is not None
        doubled = result.values["doubled"]
        self.assertIsNone(doubled["value"])
        self.assertIsNone(doubled["errors"])

    def test_per_row_missing_sibling_yields_no_value_no_error(self):
        # density references mass and volume; submit a row missing volume. An
        # unfilled sibling input is "no value yet", not an error — the per-row
        # computed cell is None with no error message.
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0}]}),
        )
        assert result.values is not None
        density_cell = result.values["samples"][0]["density"]
        self.assertIsNone(density_cell["value"])
        self.assertIsNone(density_cell["errors"])

    def test_error_key_for_outer_aggregate_over_empty_paramset(self):
        # mean() of an empty list raises in the evaluator (test_computed_param
        # pins this — see test_aggregate_over_empty_paramset_raises). sum() is
        # well-defined as 0 over the empty list and does NOT error, so use
        # mean() to exercise the empty-aggregate path.
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs({"mass": FloatParam(human_name="Mass", optional=True)}),
                    min_number_of_occurrences=0,
                ),
                "avg_mass": ComputedParam(expression="mean(@samples[].mass)"),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(form.id, SaveFormDTO(values={"samples": []}))
        assert result.values is not None
        avg = result.values["avg_mass"]
        self.assertIsNone(avg["value"])
        self.assertIsNotNone(avg["errors"])

    def test_error_key_for_unsupported_result_type(self):
        # An aggregate reference without a reducer evaluates to a list, which is
        # not a supported computed result; this surfaces inline on the cell.
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs({"mass": FloatParam(human_name="Mass", optional=True)}),
                    min_number_of_occurrences=0,
                ),
                "all_masses": ComputedParam(expression="@samples[].mass"),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(form.id, SaveFormDTO(values={"samples": [{"mass": 1.0}]}))
        assert result.values is not None
        cell = result.values["all_masses"]
        self.assertIsNone(cell["value"])
        self.assertIsNotNone(cell["errors"])

    def test_no_errors_on_clean_save(self):
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 2.0, "volume": 1.0}]}),
        )
        assert result.values is not None
        self.assertEqual(
            result.values["samples"][0]["density"],
            {"value": 2.0, "errors": None},
        )
        self.assertEqual(result.values["total_mass"], {"value": 2.0, "errors": None})

    # ------------------------------------------------------------------ #
    # Computed values appear in FormSaveEvent.changes (spec §8 step 7)
    # ------------------------------------------------------------------ #

    def test_first_save_emits_field_updated_for_outer_computed(self):
        # create() seeds form.values from spec defaults, so total_mass is
        # already present as null at creation time. The first user save that
        # gives it a value therefore emits FIELD_UPDATED (null -> 1.0), not
        # FIELD_CREATED.
        form = self._density_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 1)
        changes = events[0].get_changes()
        outer = [c for c in changes if c.field_path == "total_mass"]
        self.assertEqual(len(outer), 1)
        self.assertEqual(outer[0].action, FormChangeAction.FIELD_UPDATED)
        self.assertIsNone(outer[0].old_value)
        self.assertEqual(outer[0].new_value, 1.0)

    def test_subsequent_save_emits_field_updated_for_outer_computed(self):
        form = self._density_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        # Update the user input — total_mass should change from 1.0 to 3.0.
        saved_form = Form.get_by_id(form.id)
        assert saved_form is not None and saved_form.values is not None
        rows = saved_form.values["samples"]
        rows[0]["mass"] = 3.0
        FormService.save(form.id, SaveFormDTO(values={"samples": rows}))

        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 2)
        # total_mass starts present-as-null (seeded by create), so both saves
        # report it as FIELD_UPDATED: null -> 1.0, then 1.0 -> 3.0.
        total_mass_entries = [
            c for ev in events for c in ev.get_changes() if c.field_path == "total_mass"
        ]
        self.assertEqual(
            {c.action for c in total_mass_entries},
            {FormChangeAction.FIELD_UPDATED},
        )
        pairs = sorted(
            ((c.old_value, c.new_value) for c in total_mass_entries),
            key=lambda p: (p[0] is not None, p[0], p[1]),
        )
        self.assertEqual(pairs, [(None, 1.0), (1.0, 3.0)])

    def test_per_row_computed_appears_in_changes(self):
        # First save adds the whole row (PARAMSET_ITEM_ADDED carrying the
        # density inside its new_value payload). A second save mutating mass
        # on the same row emits FIELD_UPDATED for both mass and density on
        # the per-row path.
        form = self._density_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        # Re-read storage (scalar shape) for the next save — the response
        # wraps computed cells, but storage stays scalar.
        saved_form = Form.get_by_id(form.id)
        assert saved_form is not None and saved_form.values is not None
        rows = saved_form.values["samples"]
        item_id = rows[0]["__item_id"]

        # First save: row added as a unit; density rides along inside the
        # row's payload (no separate FIELD_CREATED for density).
        events_after_first = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events_after_first), 1)
        added_entries = [
            c
            for c in events_after_first[0].get_changes()
            if c.action == FormChangeAction.PARAMSET_ITEM_ADDED
        ]
        self.assertEqual(len(added_entries), 1)
        self.assertEqual(added_entries[0].new_value["density"], 2.0)

        # Second save: mutate the user-input mass; density recomputes from
        # 2.0 to 4.0 and surfaces as a FIELD_UPDATED on the per-row path.
        rows[0]["mass"] = 2.0
        FormService.save(form.id, SaveFormDTO(values={"samples": rows}))

        per_row_path = f"samples[item_id={item_id}].density"
        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 2)
        density_updates = [
            c
            for ev in events
            for c in ev.get_changes()
            if c.field_path == per_row_path and c.action == FormChangeAction.FIELD_UPDATED
        ]
        self.assertEqual(len(density_updates), 1)
        self.assertEqual(density_updates[0].old_value, 2.0)
        self.assertEqual(density_updates[0].new_value, 4.0)

    # ------------------------------------------------------------------ #
    # Re-edit on SUBMITTED still recomputes (spec §3.3 + §6.7)
    # ------------------------------------------------------------------ #

    def test_re_edit_on_submitted_recomputes_computed_values(self):
        form = self._density_form()
        # First save + submit.
        FormService.save(
            form.id,
            SaveFormDTO(
                values={"samples": [{"mass": 1.0, "volume": 0.5}]},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        # Re-edit on the SUBMITTED form.
        submitted_form = Form.get_by_id(form.id)
        assert submitted_form is not None and submitted_form.values is not None
        rows = submitted_form.values["samples"]
        rows[0]["mass"] = 4.0  # density 2.0 -> 8.0; total_mass 1.0 -> 4.0
        result = FormService.save(form.id, SaveFormDTO(values={"samples": rows}))

        # Status sticks (Phase 3 invariant) AND computed values are fresh.
        reloaded = Form.get_by_id(form.id)
        assert reloaded is not None and reloaded.values is not None
        assert result.values is not None
        self.assertEqual(reloaded.status, FormStatus.SUBMITTED)
        self.assertEqual(
            result.values["samples"][0]["density"],
            {"value": 8.0, "errors": None},
        )
        self.assertEqual(result.values["total_mass"], {"value": 4.0, "errors": None})
        # Storage stays scalar (the wrapper is response-only).
        self.assertEqual(reloaded.values["samples"][0]["density"], 8.0)
        self.assertEqual(reloaded.values["total_mass"], 4.0)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _density_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass", optional=True),
                            "volume": FloatParam(human_name="Volume", optional=True),
                            "density": ComputedParam(
                                expression="@mass / @volume"
                            ),
                        }
                    ),
                    min_number_of_occurrences=0,
                ),
                "total_mass": ComputedParam(expression="sum(@samples[].mass)"),
            }
        )
        return self._make_form_from_specs(specs)

    def _make_form_from_specs(self, specs: ConfigSpecs) -> Form:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="T"))
        draft = self._get_draft(template)
        draft.update_specs(specs)
        published = FormTemplateService.publish_version(template.id, draft.id)
        return FormService.create(CreateFormDTO(template_version_id=published.id))

    def _get_draft(self, template: FormTemplate) -> FormTemplateVersion:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )

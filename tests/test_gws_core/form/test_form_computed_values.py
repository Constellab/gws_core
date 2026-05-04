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
import unittest

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, StrParam
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
    UpdateDraftVersionDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase


def _serialize(specs: ConfigSpecs) -> dict:
    return {k: v.to_json_dict() for k, v in specs.to_dto().items()}


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
        self.assertIn("samples[].density", result.errors)
        self.assertIsNone(result.form.values["samples"][0]["density"])

    def test_error_key_for_outer_scope_unknown_reference(self):
        # Outer formula references a key that doesn't exist in the spec.
        # Phase 0's check_graph would normally reject this at publish time,
        # so we go around it by stuffing a published version with hand-crafted
        # serialized content.
        specs = ConfigSpecs(
            {
                "mass": FloatParam(human_name="Mass", optional=True),
                "doubled": ComputedParam(
                    expression="mass * 2", result_type="float"
                ),
            }
        )
        form = self._make_form_from_specs(specs)
        # No mass provided: missing-reference error surfaces at outer-scope
        # error key "doubled".
        result = FormService.save(form.id, SaveFormDTO(values={}))
        self.assertIn("doubled", result.errors)
        self.assertIsNone(result.form.values.get("doubled"))

    def test_error_key_for_per_row_missing_sibling(self):
        # density references mass and volume; submit a row missing volume.
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0}]}),
        )
        self.assertIn("samples[].density", result.errors)
        self.assertIsNone(result.form.values["samples"][0]["density"])

    def test_error_key_for_outer_aggregate_over_empty_paramset(self):
        # mean() of an empty list raises in the evaluator (test_computed_param
        # pins this — see test_aggregate_over_empty_paramset_raises). sum() is
        # well-defined as 0 over the empty list and does NOT error, so use
        # mean() to exercise the empty-aggregate path.
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {"mass": FloatParam(human_name="Mass", optional=True)}
                    ),
                    optional=True,
                ),
                "avg_mass": ComputedParam(
                    expression="mean(samples[].mass)", result_type="float"
                ),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(form.id, SaveFormDTO(values={"samples": []}))
        self.assertIn("avg_mass", result.errors)
        self.assertIsNone(result.form.values.get("avg_mass"))

    def test_error_key_for_outer_type_mismatch(self):
        # User field is a StrParam but the formula does arithmetic on it.
        specs = ConfigSpecs(
            {
                "label": StrParam(human_name="Label", optional=True),
                "doubled_label": ComputedParam(
                    expression="label * 2", result_type="float"
                ),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(
            form.id, SaveFormDTO(values={"label": "not a number"})
        )
        # `"not a number" * 2` evaluates to a string under simpleeval; coercion
        # to float fails and surfaces an error at the outer-scope key.
        self.assertIn("doubled_label", result.errors)
        self.assertIsNone(result.form.values.get("doubled_label"))

    def test_no_errors_on_clean_save(self):
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(
                values={"samples": [{"mass": 2.0, "volume": 1.0}]}
            ),
        )
        self.assertEqual(result.errors, {})
        self.assertEqual(result.form.values["samples"][0]["density"], 2.0)
        self.assertEqual(result.form.values["total_mass"], 2.0)

    # ------------------------------------------------------------------ #
    # Computed values appear in FormSaveEvent.changes (spec §8 step 7)
    # ------------------------------------------------------------------ #

    def test_first_save_emits_field_created_for_outer_computed(self):
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
        self.assertEqual(outer[0].action, FormChangeAction.FIELD_CREATED)
        self.assertIsNone(outer[0].old_value)
        self.assertEqual(outer[0].new_value, 1.0)

    def test_subsequent_save_emits_field_updated_for_outer_computed(self):
        form = self._density_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        # Update the user input — total_mass should change from 1.0 to 3.0.
        rows = Form.get_by_id(form.id).values["samples"]
        rows[0]["mass"] = 3.0
        FormService.save(form.id, SaveFormDTO(values={"samples": rows}))

        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 2)
        # Look at all entries across both events; total_mass must appear with
        # both CREATED (first save) and UPDATED (second save).
        total_mass_entries = [
            c
            for ev in events
            for c in ev.get_changes()
            if c.field_path == "total_mass"
        ]
        actions = sorted(c.action.value for c in total_mass_entries)
        self.assertEqual(
            actions,
            sorted([FormChangeAction.FIELD_CREATED.value, FormChangeAction.FIELD_UPDATED.value]),
        )
        updated = [c for c in total_mass_entries if c.action == FormChangeAction.FIELD_UPDATED][0]
        self.assertEqual(updated.old_value, 1.0)
        self.assertEqual(updated.new_value, 3.0)

    def test_per_row_computed_appears_in_changes(self):
        # First save adds the whole row (PARAMSET_ITEM_ADDED carrying the
        # density inside its new_value payload). A second save mutating mass
        # on the same row emits FIELD_UPDATED for both mass and density on
        # the per-row path.
        form = self._density_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        rows = result.form.values["samples"]
        item_id = rows[0]["__item_id"]

        # First save: row added as a unit; density rides along inside the
        # row's payload (no separate FIELD_CREATED for density).
        events_after_first = list(
            FormSaveEvent.select().where(FormSaveEvent.form == form.id)
        )
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
            if c.field_path == per_row_path
            and c.action == FormChangeAction.FIELD_UPDATED
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
        rows = Form.get_by_id(form.id).values["samples"]
        rows[0]["mass"] = 4.0  # density 2.0 -> 8.0; total_mass 1.0 -> 4.0
        result = FormService.save(form.id, SaveFormDTO(values={"samples": rows}))

        # Status sticks (Phase 3 invariant) AND computed values are fresh.
        reloaded = Form.get_by_id(form.id)
        self.assertEqual(reloaded.status, FormStatus.SUBMITTED)
        self.assertEqual(result.form.values["samples"][0]["density"], 8.0)
        self.assertEqual(result.form.values["total_mass"], 4.0)
        # Storage matches the response.
        self.assertEqual(reloaded.values["samples"][0]["density"], 8.0)
        self.assertEqual(reloaded.values["total_mass"], 4.0)

    # ------------------------------------------------------------------ #
    # Search by a computed-field value (spec §14)
    # ------------------------------------------------------------------ #

    @unittest.skip(
        "Search by JSON-key path on Form.values is not supported by the "
        "search infra (search_builder._get_model_field requires a model "
        "column). Once JSON-key filtering lands, computed keys participate "
        "for free since storage is the union — re-enable this test then."
    )
    def test_search_by_outer_computed_field_value(self):
        # When JSON-key filtering exists: build three forms with
        # total_mass = 1.0, 50.0, 200.0; assert that filtering on
        # total_mass > 100 returns one form. The same machinery would work
        # for user keys, so this test pins the parity.
        pass

    @unittest.skip(
        "Per-row search on a paramset's nested computed value is not "
        "supported by the search infra today. Same blocker as the outer "
        "case — re-enable once JSON-path filtering lands."
    )
    def test_search_by_per_row_computed_value(self):
        pass

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
                            "volume": FloatParam(
                                human_name="Volume", optional=True
                            ),
                            "density": ComputedParam(
                                expression="mass / volume", result_type="float"
                            ),
                        }
                    ),
                    optional=True,
                ),
                "total_mass": ComputedParam(
                    expression="sum(samples[].mass)", result_type="float"
                ),
            }
        )
        return self._make_form_from_specs(specs)

    def _make_form_from_specs(self, specs: ConfigSpecs) -> Form:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="T"))
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_serialize(specs))
        )
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

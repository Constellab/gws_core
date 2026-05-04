"""Save flow / submit / re-edit / computed values per spec §8."""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import (
    CreateFormDTO,
    FormStatus,
    SaveFormDTO,
)
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_service import FormService
from gws_core.form.form_values_service import FormValuesService
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


class TestFormSaveAndSubmit(BaseTestCase):
    # ------------------------------------------------------------------ #
    # save in DRAFT
    # ------------------------------------------------------------------ #

    def test_save_partial_values_in_draft_succeeds(self):
        form = self._scalar_form()
        result = FormService.save(form.id, SaveFormDTO(values={"name": "Alice"}))
        self.assertEqual(result.form.values["name"], "Alice")
        # mass is mandatory but unset — DRAFT save still passes.
        self.assertEqual(result.form.status, FormStatus.DRAFT)

    def test_save_assigns_item_ids_to_paramset_rows(self):
        form = self._paramset_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        rows = result.form.values["samples"]
        self.assertEqual(len(rows), 1)
        self.assertIn("__item_id", rows[0])

    def test_resave_with_no_changes_is_noop(self):
        form = self._scalar_form()
        FormService.save(form.id, SaveFormDTO(values={"name": "Alice"}))

        before = FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()
        # Re-fetch the values (with __item_ids already assigned) and resubmit.
        same_values = Form.get_by_id(form.id).values
        FormService.save(form.id, SaveFormDTO(values=same_values))
        after = FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()

        self.assertEqual(before, after)

    def test_save_invalid_type_raises(self):
        form = self._scalar_form()
        with self.assertRaises(Exception):
            FormService.save(
                form.id, SaveFormDTO(values={"mass": "not a float"})
            )

    # ------------------------------------------------------------------ #
    # submit
    # ------------------------------------------------------------------ #

    def test_submit_with_all_mandatories_set(self):
        form = self._scalar_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(
                values={"name": "Alice", "mass": 1.5},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        self.assertEqual(result.form.status, FormStatus.SUBMITTED)
        self.assertIsNotNone(result.form.submitted_at)
        self.assertIsNotNone(result.form.submitted_by)

    def test_submit_with_missing_mandatories_rejects(self):
        form = self._scalar_form()
        with self.assertRaises(BadRequestException):
            FormService.save(
                form.id,
                SaveFormDTO(
                    values={"mass": 1.5},  # name is missing
                    status_transition=FormStatus.SUBMITTED,
                ),
            )
        self.assertEqual(
            Form.get_by_id(form.id).status, FormStatus.DRAFT
        )

    def test_submit_gate_does_not_block_on_unset_computed_param(self):
        # Mandatory user field + a ComputedParam. Set the user field, then
        # submit. The submit gate must skip computed entries (they are never
        # accepted from the user) — so it succeeds even though the computed
        # field's value comes from evaluation, not from dto.values.
        specs = ConfigSpecs(
            {
                "name": StrParam(human_name="Name"),  # mandatory
                "shouted_name": ComputedParam(
                    expression='concat(name, "!")', result_type="str"
                ),
            }
        )
        form = self._make_form_from_specs(specs)
        result = FormService.save(
            form.id,
            SaveFormDTO(
                values={"name": "Alice"},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        self.assertEqual(result.form.status, FormStatus.SUBMITTED)
        self.assertEqual(result.form.values["shouted_name"], "Alice!")

    def test_submit_sugar_endpoint(self):
        form = self._scalar_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"name": "Alice", "mass": 1.5}),
        )
        result = FormService.submit(form.id)
        self.assertEqual(result.form.status, FormStatus.SUBMITTED)

    def test_resubmit_already_submitted_is_no_status_change(self):
        form = self._scalar_form()
        FormService.save(
            form.id,
            SaveFormDTO(
                values={"name": "Alice", "mass": 1.5},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        before_count = (
            FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()
        )
        FormService.submit(form.id)  # already SUBMITTED — no diff, no status change
        after_count = (
            FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()
        )
        self.assertEqual(before_count, after_count)

    # ------------------------------------------------------------------ #
    # re-edit after SUBMITTED
    # ------------------------------------------------------------------ #

    def test_re_edit_after_submitted_keeps_status(self):
        form = self._scalar_form()
        FormService.save(
            form.id,
            SaveFormDTO(
                values={"name": "Alice", "mass": 1.5},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        events_before = (
            FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()
        )

        # Edit a field on the SUBMITTED form.
        FormService.save(
            form.id,
            SaveFormDTO(values={"name": "Bob", "mass": 1.5}),
        )

        reloaded = Form.get_by_id(form.id)
        self.assertEqual(reloaded.status, FormStatus.SUBMITTED)
        self.assertEqual(reloaded.values["name"], "Bob")
        events_after = (
            FormSaveEvent.select().where(FormSaveEvent.form == form.id).count()
        )
        self.assertEqual(events_after, events_before + 1)

    # ------------------------------------------------------------------ #
    # computed values
    # ------------------------------------------------------------------ #

    def test_save_persists_computed_values_in_union(self):
        form = self._computed_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(
                values={
                    "samples": [
                        {"mass": 1.0, "volume": 0.5},
                        {"mass": 2.0, "volume": 1.0},
                    ]
                }
            ),
        )
        # Per-row computed values appear inside each row.
        rows = result.form.values["samples"]
        self.assertEqual(rows[0]["density"], 2.0)
        self.assertEqual(rows[1]["density"], 2.0)
        # Outer-scope computed value is in the same dict.
        self.assertEqual(result.form.values["total_mass"], 3.0)
        self.assertEqual(result.errors, {})

    def test_division_by_zero_returns_error_does_not_block_save(self):
        form = self._computed_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.0}]}),
        )
        # The save succeeded.
        self.assertIsNotNone(Form.get_by_id(form.id).values)
        # density failed; error key uses the per-row "<paramset>[].<field>" path.
        self.assertIn("samples[].density", result.errors)
        # density value in the row is None (failed evaluation).
        self.assertIsNone(result.form.values["samples"][0]["density"])

    def test_get_full_returns_stored_union(self):
        form = self._computed_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0, "volume": 0.5}]}),
        )
        result = FormService.get_full(form.id)
        self.assertEqual(result.form.values["samples"][0]["density"], 2.0)
        self.assertEqual(result.form.values["total_mass"], 1.0)

    def test_client_submitted_computed_value_is_stripped(self):
        form = self._computed_form()
        # Client tries to override total_mass.
        result = FormService.save(
            form.id,
            SaveFormDTO(
                values={
                    "samples": [{"mass": 1.0, "volume": 0.5}],
                    "total_mass": 9999.0,
                }
            ),
        )
        # The evaluator wins — total_mass is recomputed from sum(samples[].mass).
        self.assertEqual(result.form.values["total_mass"], 1.0)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _scalar_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "name": StrParam(human_name="Name"),
                "mass": FloatParam(human_name="Mass"),
            }
        )
        return self._make_form_from_specs(specs)

    def _paramset_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass"),
                            "volume": FloatParam(human_name="Volume", optional=True),
                        }
                    )
                )
            }
        )
        return self._make_form_from_specs(specs)

    def _computed_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass"),
                            "volume": FloatParam(human_name="Volume"),
                            "density": ComputedParam(
                                expression="mass / volume",
                                result_type="float",
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

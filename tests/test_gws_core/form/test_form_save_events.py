"""FormSaveEvent shape: one row per save with a list of FormChangeEntry,
plus get_history pagination."""
from gws_core.config.config_specs import ConfigSpecs
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
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase


class TestFormSaveEvents(BaseTestCase):
    def test_n_field_save_writes_one_row_with_n_entries(self):
        form = self._scalar_form()
        FormService.save(
            form.id,
            SaveFormDTO(values={"name": "Alice", "mass": 1.5}),
        )
        events = list(
            FormSaveEvent.select().where(FormSaveEvent.form == form.id)
        )
        self.assertEqual(len(events), 1)
        actions = [c.action for c in events[0].get_changes()]
        self.assertEqual(
            sorted(actions, key=lambda a: a.value),
            sorted(
                [FormChangeAction.FIELD_CREATED, FormChangeAction.FIELD_CREATED],
                key=lambda a: a.value,
            ),
        )

    def test_noop_save_writes_zero_rows(self):
        form = self._scalar_form()
        FormService.save(form.id, SaveFormDTO(values={"name": "Alice"}))

        same_values = Form.get_by_id(form.id).values
        FormService.save(form.id, SaveFormDTO(values=same_values))

        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 1)

    def test_field_actions(self):
        # Three saves over the same form. Assert each save's individual
        # change list rather than reading events back from the DB by
        # created_at — DateTimeUTC has second-level precision, so three
        # back-to-back saves get the same timestamp and the in-second
        # ordering is not stable.
        form = self._scalar_form()
        # 1st save: name CREATED
        FormService.save(form.id, SaveFormDTO(values={"name": "Alice"}))
        # 2nd save: name UPDATED + mass CREATED
        FormService.save(
            form.id, SaveFormDTO(values={"name": "Bob", "mass": 1.0})
        )
        # 3rd save: mass DELETED
        FormService.save(form.id, SaveFormDTO(values={"name": "Bob"}))

        events = list(
            FormSaveEvent.select().where(FormSaveEvent.form == form.id)
        )
        self.assertEqual(len(events), 3)

        # Each FormChangeAction should appear at least once across the 3 saves.
        all_actions = []
        for ev in events:
            all_actions.extend(c.action for c in ev.get_changes())
        self.assertIn(FormChangeAction.FIELD_CREATED, all_actions)
        self.assertIn(FormChangeAction.FIELD_UPDATED, all_actions)
        self.assertIn(FormChangeAction.FIELD_DELETED, all_actions)

    def test_paramset_item_added_and_removed(self):
        form = self._paramset_form()
        result = FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [{"mass": 1.0}, {"mass": 2.0}]}),
        )
        rows = result.form.values["samples"]
        # remove the first row
        FormService.save(
            form.id,
            SaveFormDTO(values={"samples": [rows[1]]}),
        )

        # Aggregate across all events instead of relying on order — back-to-back
        # saves can land in the same second (DateTimeUTC has second precision)
        # and in-second ordering isn't stable.
        events = list(
            FormSaveEvent.select().where(FormSaveEvent.form == form.id)
        )
        all_actions = []
        for ev in events:
            all_actions.extend(c.action for c in ev.get_changes())
        self.assertEqual(
            all_actions.count(FormChangeAction.PARAMSET_ITEM_ADDED), 2
        )
        self.assertEqual(
            all_actions.count(FormChangeAction.PARAMSET_ITEM_REMOVED), 1
        )

    def test_status_changed_entry_on_submit(self):
        form = self._scalar_form()
        FormService.save(
            form.id,
            SaveFormDTO(
                values={"name": "Alice"},
                status_transition=FormStatus.SUBMITTED,
            ),
        )
        events = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(len(events), 1)
        changes = events[0].get_changes()
        actions = [c.action for c in changes]
        self.assertIn(FormChangeAction.STATUS_CHANGED, actions)
        status_entry = [c for c in changes if c.action == FormChangeAction.STATUS_CHANGED][0]
        self.assertEqual(status_entry.field_path, "__status")
        self.assertEqual(status_entry.old_value, FormStatus.DRAFT.value)
        self.assertEqual(status_entry.new_value, FormStatus.SUBMITTED.value)

    # ------------------------------------------------------------------ #
    # history pagination
    # ------------------------------------------------------------------ #

    def test_history_returns_events_in_descending_order(self):
        form = self._scalar_form()
        FormService.save(form.id, SaveFormDTO(values={"name": "a"}))
        FormService.save(form.id, SaveFormDTO(values={"name": "b"}))
        FormService.save(form.id, SaveFormDTO(values={"name": "c"}))

        page = FormService.get_history(form.id, page=0, number_of_items_per_page=20)
        events = list(page.results)
        self.assertEqual(len(events), 3)
        # newest first
        self.assertGreaterEqual(events[0].created_at, events[1].created_at)
        self.assertGreaterEqual(events[1].created_at, events[2].created_at)

    def test_history_pagination(self):
        form = self._scalar_form()
        for i in range(5):
            FormService.save(form.id, SaveFormDTO(values={"name": f"v{i}"}))

        page_0 = FormService.get_history(form.id, page=0, number_of_items_per_page=2)
        page_1 = FormService.get_history(form.id, page=1, number_of_items_per_page=2)

        self.assertEqual(len(list(page_0.results)), 2)
        self.assertEqual(len(list(page_1.results)), 2)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _scalar_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "name": StrParam(human_name="Name"),
                "mass": FloatParam(human_name="Mass", optional=True),
            }
        )
        return self._make_form_from_specs(specs)

    def _paramset_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs({"mass": FloatParam(human_name="Mass")}),
                    optional=True,
                )
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

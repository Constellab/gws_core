"""Reconciliation between NoteTemplate rich-text content and the
NoteTemplateFormTemplateModel join.

Phase 7 / spec §3.6.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.model.event.event_dispatcher import EventDispatcher
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_form_template_model import (
    NoteTemplateFormTemplateModel,
)
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


def _name_specs() -> ConfigSpecs:
    return ConfigSpecs({"name": StrParam(human_name="name", optional=True)})


class TestNoteTemplateFormTemplateReconciliation(BaseTestCase):

    def test_insert_form_template_block_creates_join_row(self):
        version = self._published_version("FT")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        rows = NoteTemplateFormTemplateModel.get_by_note_template(note_tpl.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].form_template_version_id, version.id)
        self.assertEqual(rows[0].form_template_id, version.template_id)

    def test_remove_form_template_block_removes_join_row(self):
        version = self._published_version("FT")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        NoteTemplateService.update_content(
            note_tpl.id, RichText.create_rich_text_dto([])
        )
        self.assertEqual(
            NoteTemplateFormTemplateModel.get_by_note_template(note_tpl.id), []
        )

    def test_denormalized_form_template_matches_version(self):
        version = self._published_version("FT")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        rows = NoteTemplateFormTemplateModel.get_by_note_template(note_tpl.id)
        self.assertEqual(rows[0].form_template_id, version.template_id)

    def test_listener_is_registered_on_note_template_content_updated_event(self):
        listeners = EventDispatcher.get_instance().get_registered_listeners()
        names = {type(l).__name__ for l in listeners}
        self.assertIn("NoteTemplateFormTemplateJoinListener", names)

    def _published_version(self, name: str) -> FormTemplateVersion:
        template = FormTemplateService.create(CreateFormTemplateDTO(name=name))
        draft = (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )
        draft.update_specs(_name_specs())
        return FormTemplateService.publish_version(template.id, draft.id)

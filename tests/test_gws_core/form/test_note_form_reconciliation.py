"""Reconciliation between rich-text content and the NoteFormModel join,
driven by NoteContentUpdatedEvent listeners.

Phase 7 / spec §3.6.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from gws_core.model.event.event_dispatcher import EventDispatcher
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    InsertNewFormBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_events import NoteContentUpdatedEvent
from gws_core.note.note_form_model import NoteFormModel
from gws_core.note.note_service import NoteService
from gws_core.test.base_test_case import BaseTestCase


def _name_specs() -> ConfigSpecs:
    return ConfigSpecs({"name": StrParam(human_name="name", optional=True)})


class TestNoteFormReconciliation(BaseTestCase):

    # ---------------- Insert / remove via service routes -----------------

    def test_insert_form_block_creates_join_row(self):
        version = self._published_version("T")
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_new(
            note.id,
            InsertNewFormBlockDTO(template_version_id=version.id),
        )
        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_owner)

    def test_insert_reference_block_creates_join_row_with_is_owner_false(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].form_id, form.id)
        self.assertFalse(rows[0].is_owner)

    def test_remove_form_block_removes_join_row(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        # Strip the FORM block by replacing content with an empty body.
        NoteService.update_content(note.id, RichText.create_rich_text_dto([]))
        self.assertEqual(NoteFormModel.get_by_note(note.id), [])

    def test_update_content_with_changed_is_owner_updates_join_row(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        # Build a content with the same form_id but is_owner=True.
        block = RichTextBlock.from_data(
            RichTextBlockForm(form_id=form.id, is_owner=True, display_name=None)
        )
        rich_text = RichText.create_rich_text_dto([block.to_json_dict()])
        # Mutate via the dispatcher contract — note content must accept
        # this through update_content; the validator allows existing
        # form_ids.
        NoteService.update_content(note.id, rich_text)

        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_owner)

    def test_two_form_blocks_for_same_form_in_one_note_collapse_to_one_row(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        # Insert the same form twice via reference.
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)

    # ---------------- Cascade / RESTRICT ----------------------------------

    def test_cascade_on_note_delete_drops_join_rows(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        self.assertEqual(len(NoteFormModel.get_by_note(note.id)), 1)
        NoteService.delete(note.id)
        # The note is gone; rows survived only if FK CASCADE didn't fire,
        # which would also have made the cascade-delete listener trip.
        self.assertEqual(NoteFormModel.get_by_note(note.id), [])

    # ---------------- Listener registration footgun -----------------------

    def test_listener_is_registered_on_note_content_updated_event(self):
        listeners = EventDispatcher.get_instance().get_registered_listeners()
        names = {type(l).__name__ for l in listeners}
        self.assertIn("NoteFormJoinListener", names)
        self.assertIn("FormNoteCascadeListener", names)

    # ---------------- Helpers --------------------------------------------

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

    def _make_form(self):
        version = self._published_version("Demo")
        return FormService.create(CreateFormDTO(template_version_id=version.id))

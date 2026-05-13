"""Cascade-on-note-delete tests for the §5.6 contract:

- An owner-only Form is deleted with its owning Note.
- A referenced (is_owner=False) Form survives.
- An owned Form with other (non-owner) references survives.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.form.form import Form
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    InsertNewFormBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_form_model import NoteFormModel
from gws_core.note.note_service import NoteService
from gws_core.test.base_test_case import BaseTestCase


def _name_specs() -> ConfigSpecs:
    return ConfigSpecs({"name": StrParam(human_name="name", optional=True)})


class TestNoteDeleteFormCascade(BaseTestCase):

    def test_delete_note_deletes_owned_form(self):
        version = self._published_version("T")
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_new(
            note.id, InsertNewFormBlockDTO(template_version_id=version.id)
        )
        owned_form_id = NoteFormModel.get_by_note(note.id)[0].form_id

        NoteService.delete(note.id)

        self.assertIsNone(Form.get_by_id(owned_form_id))

    def test_delete_note_cascades_form_save_events(self):
        version = self._published_version("T")
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_new(
            note.id, InsertNewFormBlockDTO(template_version_id=version.id)
        )
        owned_form_id = NoteFormModel.get_by_note(note.id)[0].form_id
        # Drop a save event row directly so we don't need the full save flow.
        form = Form.get_by_id_and_check(owned_form_id)
        evt = FormSaveEvent()
        evt.form = form
        evt.user = form.created_by
        evt.set_changes([])
        evt.save()

        NoteService.delete(note.id)

        self.assertIsNone(Form.get_by_id(owned_form_id))
        remaining = list(FormSaveEvent.select().where(FormSaveEvent.form == owned_form_id))
        self.assertEqual(remaining, [])

    def test_delete_note_preserves_referenced_only_form(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        NoteService.delete(note.id)
        self.assertIsNotNone(Form.get_by_id(form.id))

    def test_delete_note_preserves_owned_form_with_other_references(self):
        # Note A owns form F; Note B references F.
        version = self._published_version("T")
        note_a = NoteService.create(NoteSaveDTO(title="A"))
        NoteService.insert_form_block_new(
            note_a.id, InsertNewFormBlockDTO(template_version_id=version.id)
        )
        owned_form_id = NoteFormModel.get_by_note(note_a.id)[0].form_id

        note_b = NoteService.create(NoteSaveDTO(title="B"))
        NoteService.insert_form_block_reference(
            note_b.id, InsertFormReferenceBlockDTO(form_id=owned_form_id)
        )

        NoteService.delete(note_a.id)

        self.assertIsNotNone(Form.get_by_id(owned_form_id))
        # Note B's reference row survives.
        rows = NoteFormModel.get_by_note(note_b.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].form_id, owned_form_id)
        self.assertFalse(rows[0].is_owner)

    def test_delete_note_with_mixed_owner_and_reference_blocks(self):
        version = self._published_version("T")
        other_form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_new(
            note.id, InsertNewFormBlockDTO(template_version_id=version.id)
        )
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=other_form.id)
        )
        owned_id = next(
            r.form_id for r in NoteFormModel.get_by_note(note.id) if r.is_owner
        )

        NoteService.delete(note.id)

        # Owned form gone; referenced form survives.
        self.assertIsNone(Form.get_by_id(owned_id))
        self.assertIsNotNone(Form.get_by_id(other_form.id))

    def test_delete_note_without_form_blocks_is_unaffected(self):
        # Snapshot the form count, delete a note with no FORM blocks,
        # confirm the count is unchanged (test isolation can't be
        # assumed across test methods in the same class run).
        before = Form.select().count()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.delete(note.id)
        self.assertEqual(Form.select().count(), before)

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

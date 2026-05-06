"""Rollback path: when a Note's content is restored from history, the
form-join listener reconciles NoteFormModel rows against the rolled-back
content. The validator deliberately does NOT run on this path so that
rollback can resurrect blocks whose targets were hard-deleted in the
meantime.

The rollback function (NoteService.rollback_content) delegates undo-
content computation to an external Space API, so end-to-end tests are
expensive. These tests pin the *contract* that matters: dispatching
NoteContentUpdatedEvent reconciles the join, and the validator is only
invoked when callers explicitly call it (which rollback no longer does).
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.form.form import Form
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from gws_core.model.event.event_dispatcher import EventDispatcher
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_events import NoteContentUpdatedEvent
from gws_core.note.note_form_model import NoteFormModel
from gws_core.note.note_service import NoteService
from gws_core.test.base_test_case import BaseTestCase


def _name_specs() -> ConfigSpecs:
    return ConfigSpecs({"name": StrParam(human_name="name", optional=True)})


class TestNoteRollbackFormReconciliation(BaseTestCase):

    # ---------------- Forward direction ----------------

    def test_dispatching_rollback_event_with_added_form_block_creates_join(self):
        # Simulate a rollback that restores a content state containing a
        # FORM block. The note currently has no FORM blocks; after the
        # synthetic dispatch, NoteFormModel has the row.
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        self.assertEqual(NoteFormModel.get_by_note(note.id), [])

        block = RichTextBlock.from_data(
            RichTextBlockForm(form_id=form.id, is_owner=False, display_name=None)
        )
        rolled_back = RichText.create_rich_text_dto([block])

        EventDispatcher.get_instance().dispatch(
            NoteContentUpdatedEvent(
                note_id=note.id,
                old_content=note.content,
                new_content=rolled_back,
            )
        )

        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].form_id, form.id)
        self.assertFalse(rows[0].is_owner)

    def test_dispatching_rollback_event_with_removed_form_block_removes_join(self):
        # Note currently has a FORM block; simulate rollback to a state
        # without it.
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        self.assertEqual(len(NoteFormModel.get_by_note(note.id)), 1)

        rolled_back = RichText.create_rich_text_dto([])
        EventDispatcher.get_instance().dispatch(
            NoteContentUpdatedEvent(
                note_id=note.id,
                old_content=note.refresh().content,
                new_content=rolled_back,
            )
        )

        self.assertEqual(NoteFormModel.get_by_note(note.id), [])

    # ---------------- Deleted-target corner case ----------------

    def test_rollback_event_with_deleted_form_id_still_reconciles(self):
        # The whole point of option 2: rollback can resurrect a block
        # whose form_id was hard-deleted in the meantime. The listener
        # writes the join row anyway (so the content is the source of
        # truth) and the FK RESTRICT is the safety net for the next
        # form-side delete attempt.
        #
        # Here we mimic that by referencing a never-existed form id. The
        # FK insert will fail (RESTRICT against a missing form row),
        # which is the desired behavior — the join cannot point at a
        # ghost. We assert the listener reaches the FK layer rather than
        # bouncing off the validator early.
        note = NoteService.create(NoteSaveDTO(title="N"))
        block = RichTextBlock.from_data(
            RichTextBlockForm(
                form_id="never-existed",
                is_owner=False,
                display_name=None,
            )
        )
        rolled_back = RichText.create_rich_text_dto([block])

        # Listener will attempt to upsert a row pointing at a non-existent
        # Form; expect a DB-level error, not a validator BadRequest.
        with self.assertRaises(Exception) as ctx:
            EventDispatcher.get_instance().dispatch(
                NoteContentUpdatedEvent(
                    note_id=note.id,
                    old_content=note.content,
                    new_content=rolled_back,
                )
            )
        # The error must come from the DB layer, NOT from the validator
        # (the validator is not in this code path).
        self.assertNotIn("validator", str(ctx.exception).lower())
        self.assertNotIn("FORM block references unknown", str(ctx.exception))

    # ---------------- Helpers ----------------

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

    def _make_form(self) -> Form:
        version = self._published_version("Demo")
        return FormService.create(CreateFormDTO(template_version_id=version.id))

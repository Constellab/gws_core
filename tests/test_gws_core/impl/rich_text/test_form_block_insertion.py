"""Insertion endpoints + context gating + reference validity for FORM_TEMPLATE
and FORM blocks (Phase 6)."""

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.exception.exceptions.not_found_exception import (
    NotFoundException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    UpdateDraftVersionDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    InsertNewFormBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_service import NoteService
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict() -> dict:
    specs = ConfigSpecs({"name": StrParam(human_name="Name")}).to_dto()
    return {k: v.to_json_dict() for k, v in specs.items()}


class TestFormBlockInsertion(BaseTestCase):

    # ------------------------------------------------------------------ #
    # FORM_TEMPLATE in NoteTemplate
    # ------------------------------------------------------------------ #

    def test_insert_form_template_block_succeeds(self):
        version = self._published_version()
        note_template = NoteTemplateService.create_empty("nt")

        updated = NoteTemplateService.insert_form_template_block(
            note_template.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )

        ft_blocks = [
            b for b in updated.content.blocks
            if b.is_type(RichTextBlockTypeStandard.FORM_TEMPLATE)
        ]
        self.assertEqual(len(ft_blocks), 1)
        data = ft_blocks[0].get_data()
        self.assertEqual(data.form_template_version_id, version.id)
        self.assertEqual(data.form_template_id, version.template_id)

    def test_insert_form_template_block_rejected_for_draft_version(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="t"))
        draft = self._get_draft(template)
        # Draft has no published version yet; the version itself is DRAFT.
        note_template = NoteTemplateService.create_empty("nt")

        with self.assertRaises(BadRequestException):
            NoteTemplateService.insert_form_template_block(
                note_template.id,
                InsertFormTemplateBlockDTO(form_template_version_id=draft.id),
            )

    def test_insert_form_template_block_rejected_for_archived_version(self):
        version = self._published_version()
        FormTemplateService.archive_version(version.template_id, version.id)

        note_template = NoteTemplateService.create_empty("nt")
        with self.assertRaises(BadRequestException):
            NoteTemplateService.insert_form_template_block(
                note_template.id,
                InsertFormTemplateBlockDTO(form_template_version_id=version.id),
            )

    def test_form_template_block_in_note_template_survives_archive(self):
        """Once a FORM_TEMPLATE block is in place, archiving its pinned
        version must not break subsequent saves of the NoteTemplate
        (validator only re-checks newly-introduced blocks)."""
        version = self._published_version()
        note_template = NoteTemplateService.create_empty("nt")
        NoteTemplateService.insert_form_template_block(
            note_template.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )

        FormTemplateService.archive_version(version.template_id, version.id)

        # Re-saving the same content should still succeed.
        nt = NoteTemplateService.get_by_id_and_check(note_template.id)
        NoteTemplateService.update_content(note_template.id, nt.content)

    # ------------------------------------------------------------------ #
    # FORM in Note
    # ------------------------------------------------------------------ #

    def test_insert_form_block_new_creates_form_and_owner_block(self):
        version = self._published_version()
        note = NoteService.create(NoteSaveDTO(title="n"))

        updated = NoteService.insert_form_block_new(
            note.id,
            InsertNewFormBlockDTO(template_version_id=version.id),
        )

        form_blocks = [
            b for b in updated.content.blocks
            if b.is_type(RichTextBlockTypeStandard.FORM)
        ]
        self.assertEqual(len(form_blocks), 1)
        data: RichTextBlockForm = form_blocks[0].get_data()
        self.assertTrue(data.is_owner)
        # The referenced form actually exists.
        self.assertIsNotNone(Form.get_by_id(data.form_id))

    def test_insert_form_block_reference_uses_existing_form(self):
        version = self._published_version()
        existing_form = FormService.create(
            CreateFormDTO(template_version_id=version.id)
        )
        note = NoteService.create(NoteSaveDTO(title="n"))

        before_count = Form.select().count()
        updated = NoteService.insert_form_block_reference(
            note.id,
            InsertFormReferenceBlockDTO(form_id=existing_form.id),
        )
        after_count = Form.select().count()
        # No new Form was created.
        self.assertEqual(before_count, after_count)

        form_blocks = [
            b for b in updated.content.blocks
            if b.is_type(RichTextBlockTypeStandard.FORM)
        ]
        self.assertEqual(len(form_blocks), 1)
        data: RichTextBlockForm = form_blocks[0].get_data()
        self.assertFalse(data.is_owner)
        self.assertEqual(data.form_id, existing_form.id)

    def test_insert_form_block_reference_rejected_for_unknown_form(self):
        note = NoteService.create(NoteSaveDTO(title="n"))
        with self.assertRaises(NotFoundException):
            NoteService.insert_form_block_reference(
                note.id,
                InsertFormReferenceBlockDTO(form_id="does-not-exist"),
            )

    def test_two_notes_can_reference_same_form(self):
        version = self._published_version()
        existing_form = FormService.create(
            CreateFormDTO(template_version_id=version.id)
        )
        note_a = NoteService.create(NoteSaveDTO(title="A"))
        note_b = NoteService.create(NoteSaveDTO(title="B"))

        NoteService.insert_form_block_reference(
            note_a.id, InsertFormReferenceBlockDTO(form_id=existing_form.id)
        )
        NoteService.insert_form_block_reference(
            note_b.id, InsertFormReferenceBlockDTO(form_id=existing_form.id)
        )

        a = NoteService.get_by_id_and_check(note_a.id)
        b = NoteService.get_by_id_and_check(note_b.id)
        a_form_id = next(
            blk.get_data().form_id for blk in a.content.blocks
            if blk.is_type(RichTextBlockTypeStandard.FORM)
        )
        b_form_id = next(
            blk.get_data().form_id for blk in b.content.blocks
            if blk.is_type(RichTextBlockTypeStandard.FORM)
        )
        self.assertEqual(a_form_id, b_form_id)
        self.assertEqual(a_form_id, existing_form.id)

    def test_position_param_inserts_at_index(self):
        version = self._published_version()
        note = NoteService.create(NoteSaveDTO(title="n"))
        first_block_count = len(note.content.blocks)

        # Insert at position 0 — should land at the very start.
        updated = NoteService.insert_form_block_new(
            note.id,
            InsertNewFormBlockDTO(template_version_id=version.id, position=0),
        )
        self.assertEqual(len(updated.content.blocks), first_block_count + 1)
        self.assertTrue(updated.content.blocks[0].is_type(RichTextBlockTypeStandard.FORM))

    # ------------------------------------------------------------------ #
    # Context gating
    # ------------------------------------------------------------------ #

    def test_form_template_block_in_note_is_rejected(self):
        version = self._published_version()
        note = NoteService.create(NoteSaveDTO(title="n"))

        # Hand-craft a content payload with a FORM_TEMPLATE block in a Note.
        rich_text = note.get_content_as_rich_text()
        ft_data = RichTextBlockFormTemplate(
            form_template_id=version.template_id,
            form_template_version_id=version.id,
        )
        rich_text.append_block(RichTextBlock.from_data(ft_data))

        with self.assertRaises(BadRequestException):
            NoteService.update_content(note.id, rich_text.to_dto())

    def test_form_block_in_note_template_is_rejected(self):
        version = self._published_version()
        existing_form = FormService.create(
            CreateFormDTO(template_version_id=version.id)
        )
        note_template = NoteTemplateService.create_empty("nt")

        rich_text = note_template.get_content_as_rich_text()
        form_data = RichTextBlockForm(form_id=existing_form.id, is_owner=False)
        rich_text.append_block(RichTextBlock.from_data(form_data))

        with self.assertRaises(BadRequestException):
            NoteTemplateService.update_content(note_template.id, rich_text.to_dto())

    def test_existing_form_block_round_trips_through_update_content(self):
        """Re-saving a Note that already contains a valid FORM block works."""
        version = self._published_version()
        note = NoteService.create(NoteSaveDTO(title="n"))
        note = NoteService.insert_form_block_new(
            note.id, InsertNewFormBlockDTO(template_version_id=version.id)
        )

        # Re-save the same content; validator should pass.
        NoteService.update_content(note.id, note.content)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _published_version(self) -> FormTemplateVersion:
        template: FormTemplate = FormTemplateService.create(
            CreateFormTemplateDTO(name="t")
        )
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_spec_dict())
        )
        return FormTemplateService.publish_version(template.id, draft.id)

    def _get_draft(self, template: FormTemplate) -> FormTemplateVersion:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )

"""End-to-end §5.4 conversion tests: NoteTemplate with FORM_TEMPLATE blocks
becomes a Note with owned FORM blocks at instantiation time.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import FormStatus
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
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from gws_core.note.note_dto import NoteInsertTemplateDTO, NoteSaveDTO
from gws_core.note.note_form_model import NoteFormModel
from gws_core.note.note_service import NoteService
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict() -> dict:
    spec = ConfigSpecs({"name": StrParam(human_name="name", optional=True)}).to_dto()
    return {k: v.to_json_dict() for k, v in spec.items()}


class TestNoteTemplateFormInstantiation(BaseTestCase):

    def test_create_note_from_template_with_one_form_template_block(self):
        version = self._published_version("Sample collection")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(
                form_template_version_id=version.id,
                display_name="Pinned",
            ),
        )
        note = NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))

        rich_text = note.get_content_as_rich_text()
        self.assertEqual(
            len(rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM_TEMPLATE)),
            0,
        )
        form_blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        self.assertEqual(len(form_blocks), 1)

        data: RichTextBlockForm = form_blocks[0].get_data()
        self.assertTrue(data.is_owner)
        self.assertEqual(data.display_name, "Pinned")
        new_form = Form.get_by_id_and_check(data.form_id)
        self.assertEqual(new_form.status, FormStatus.DRAFT)
        self.assertEqual(new_form.name, version.template.name)

        rows = NoteFormModel.get_by_note(note.id)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_owner)
        self.assertEqual(rows[0].form_id, data.form_id)

    def test_create_note_from_template_with_two_form_template_blocks(self):
        v1 = self._published_version("A")
        v2 = self._published_version("B")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id, InsertFormTemplateBlockDTO(form_template_version_id=v1.id)
        )
        NoteTemplateService.insert_form_template_block(
            note_tpl.id, InsertFormTemplateBlockDTO(form_template_version_id=v2.id)
        )
        note = NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))

        rich_text = note.get_content_as_rich_text()
        form_blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        self.assertEqual(len(form_blocks), 2)
        ids = {b.get_data().form_id for b in form_blocks}
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(NoteFormModel.get_by_note(note.id)), 2)

    def test_create_note_from_template_preserves_other_blocks(self):
        version = self._published_version("FT")
        note_tpl = NoteTemplateService.create_empty("title")

        rich_text = RichText()
        rich_text.add_paragraph("first")
        rich_text.add_paragraph("second")
        NoteTemplateService.update_content(note_tpl.id, rich_text.to_dto())

        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(
                form_template_version_id=version.id, position=1
            ),
        )

        note = NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))
        blocks = note.get_content_as_rich_text().get_blocks()
        types = [b.type for b in blocks]
        self.assertEqual(types.count("paragraph"), 2)
        self.assertEqual(types.count(RichTextBlockTypeStandard.FORM.value), 1)

    def test_insert_template_into_existing_note_also_converts(self):
        version = self._published_version("FT")
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )

        note = NoteService.create(NoteSaveDTO(title="N"))
        # Existing-note content path.
        NoteService.insert_template(
            note.id,
            NoteInsertTemplateDTO(block_index=0, note_template_id=note_tpl.id),
        )
        rich_text = note.refresh().get_content_as_rich_text()
        form_blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        self.assertEqual(len(form_blocks), 1)
        self.assertTrue(form_blocks[0].get_data().is_owner)
        self.assertEqual(len(NoteFormModel.get_by_note(note.id)), 1)

    def test_archived_version_falls_back_to_current_published(self):
        # Build template with v1 PUBLISHED, then create v2 PUBLISHED, then
        # archive v1. NoteTemplate's FORM_TEMPLATE block pins v1.
        v1 = self._published_version("F")
        template_id = v1.template_id
        # Pin v1 in a NoteTemplate while it's still published.
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=v1.id),
        )
        # Ship v2.
        v2_draft = FormTemplateService.create_draft(template_id)
        FormTemplateService.update_draft(
            template_id, v2_draft.id, UpdateDraftVersionDTO(content=_spec_dict())
        )
        v2 = FormTemplateService.publish_version(template_id, v2_draft.id)
        # Archive v1. The NoteTemplateFormTemplateModel join still points
        # at v1 (the block payload didn't change), but RESTRICT FK on the
        # join lets us archive (not delete) v1, and the conversion picks
        # the current published version (v2) at instantiation time.
        FormTemplateService.archive_version(template_id, v1.id)

        note = NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))
        rich_text = note.get_content_as_rich_text()
        form_blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        self.assertEqual(len(form_blocks), 1)
        new_form = Form.get_by_id_and_check(form_blocks[0].get_data().form_id)
        self.assertEqual(new_form.template_version_id, v2.id)

    def test_archived_with_no_published_aborts(self):
        # Inject a FORM_TEMPLATE block pointing at an ARCHIVED version
        # whose template has no current published version. The
        # validator gates this on insertion (PUBLISHED required), so we
        # simulate the archived-after-insert state by direct content
        # mutation through the listener-aware path.
        v1 = self._published_version("F")
        template_id = v1.template_id
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=v1.id),
        )
        FormTemplateService.archive_version(template_id, v1.id)
        # No fallback published version exists for this family.
        with self.assertRaises(BadRequestException):
            NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))

    def test_template_with_no_form_template_blocks_is_unchanged(self):
        note_tpl = NoteTemplateService.create_empty("title")
        rich_text = RichText()
        rich_text.add_paragraph("only text")
        NoteTemplateService.update_content(note_tpl.id, rich_text.to_dto())

        note = NoteService.create(NoteSaveDTO(title="N", template_id=note_tpl.id))
        types = [b.type for b in note.get_content_as_rich_text().get_blocks()]
        self.assertEqual(types, ["paragraph"])
        self.assertEqual(NoteFormModel.get_by_note(note.id), [])

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
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_spec_dict())
        )
        return FormTemplateService.publish_version(template.id, draft.id)

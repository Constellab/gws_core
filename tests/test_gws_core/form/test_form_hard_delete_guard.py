"""Hard-delete guards on Form / FormTemplateVersion that depend on the
NoteFormModel / NoteTemplateFormTemplateModel join rows.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    UpdateDraftVersionDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_service import NoteService
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict() -> dict:
    spec = ConfigSpecs({"name": StrParam(human_name="name", optional=True)}).to_dto()
    return {k: v.to_json_dict() for k, v in spec.items()}


class TestFormHardDeleteGuard(BaseTestCase):

    def test_hard_delete_succeeds_when_no_notes_reference_form(self):
        form = self._make_form()
        FormService.hard_delete(form.id)
        self.assertIsNone(Form.get_by_id(form.id))

    def test_hard_delete_rejected_when_referenced_by_note(self):
        form = self._make_form()
        note = NoteService.create(NoteSaveDTO(title="N"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )

        with self.assertRaises(BadRequestException) as ctx:
            FormService.hard_delete(form.id)
        self.assertIn(note.title, str(ctx.exception))

    def test_form_template_version_hard_delete_rejected_when_pinned(self):
        version = self._published_version("FT")
        # Pin in a NoteTemplate.
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        # Archive then attempt delete; the join still pins it.
        FormTemplateService.archive_version(version.template_id, version.id)
        with self.assertRaises(BadRequestException):
            FormTemplateService.delete_version(version.template_id, version.id)

    def test_form_template_hard_delete_rejected_when_pinned_by_note_template(self):
        version = self._published_version("FT")
        template_id = version.template_id
        note_tpl = NoteTemplateService.create_empty("title")
        NoteTemplateService.insert_form_template_block(
            note_tpl.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        with self.assertRaises(BadRequestException):
            FormTemplateService.hard_delete(template_id)

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

    def _make_form(self):
        version = self._published_version("Demo")
        return FormService.create(CreateFormDTO(template_version_id=version.id))

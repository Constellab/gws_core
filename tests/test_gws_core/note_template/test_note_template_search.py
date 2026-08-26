from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.search_builder import (
    SearchFilterCriteria,
    SearchOperator,
    SearchParams,
)
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note_template.note_template_dto import InsertFormTemplateBlockDTO
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.test.base_test_case import BaseTestCase


# test_note_template_search
class TestNoteTemplateSearch(BaseTestCase):

    def test_search_by_form_template_id(self):
        version = self._published_version("FT")
        other_version = self._published_version("Other")

        note_target = NoteTemplateService.create_empty("target")
        NoteTemplateService.insert_form_template_block(
            note_target.id,
            InsertFormTemplateBlockDTO(form_template_version_id=version.id),
        )
        note_other = NoteTemplateService.create_empty("other")
        NoteTemplateService.insert_form_template_block(
            note_other.id,
            InsertFormTemplateBlockDTO(form_template_version_id=other_version.id),
        )
        NoteTemplateService.create_empty("empty")

        params = SearchParams(
            filtersCriteria=[
                SearchFilterCriteria(
                    key="form_template_id",
                    operator=SearchOperator.EQ,
                    value=version.template_id,
                )
            ]
        )
        page = NoteTemplateService.search(params)
        ids = [n.id for n in page.results]
        self.assertEqual(ids, [note_target.id])

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
        draft.update_specs(ConfigSpecs({"name": StrParam(human_name="name", optional=True)}))
        return FormTemplateService.publish_version(template.id, draft.id)

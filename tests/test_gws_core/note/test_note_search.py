from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchFilterCriteria, SearchOperator, SearchParams
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note.note_dto import (
    InsertFormReferenceBlockDTO,
    NoteSaveDTO,
)
from gws_core.note.note_service import NoteService
from gws_core.test.base_test_case import BaseTestCase


# test_note_search
class TestNoteSearch(BaseTestCase):
    def test_note_search(self):
        note_1 = NoteService.create(NoteSaveDTO(title="The first note"))
        NoteService.create(NoteSaveDTO(title="Another text to explain scenario"))

        search_dict: SearchParams = SearchParams()

        # Test title search
        search_dict.set_filters_criteria(
            [SearchFilterCriteria(key="title", operator=SearchOperator.CONTAINS, value="first")]
        )
        self._search(search_dict, 1)

        # test search name
        paginator: Paginator = NoteService.search_by_name("first")
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, note_1.id)

    def test_search_by_form_id(self):
        version = self._published_version("Demo")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))
        other_form = FormService.create(CreateFormDTO(template_version_id=version.id))

        note_with_form = NoteService.create(NoteSaveDTO(title="With form"))
        NoteService.insert_form_block_reference(
            note_with_form.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        note_with_other = NoteService.create(NoteSaveDTO(title="With other"))
        NoteService.insert_form_block_reference(
            note_with_other.id, InsertFormReferenceBlockDTO(form_id=other_form.id)
        )
        NoteService.create(NoteSaveDTO(title="No form"))

        params = SearchParams(
            filtersCriteria=[
                SearchFilterCriteria(
                    key="form_id", operator=SearchOperator.EQ, value=form.id
                )
            ]
        )
        page = NoteService.search(params)
        ids = [n.id for n in page.results]
        self.assertEqual(ids, [note_with_form.id])

    def test_search_by_form_template_id(self):
        version = self._published_version("Demo")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))
        other_version = self._published_version("Other")
        other_form = FormService.create(
            CreateFormDTO(template_version_id=other_version.id)
        )

        note_target = NoteService.create(NoteSaveDTO(title="Target"))
        NoteService.insert_form_block_reference(
            note_target.id, InsertFormReferenceBlockDTO(form_id=form.id)
        )
        note_other = NoteService.create(NoteSaveDTO(title="Other"))
        NoteService.insert_form_block_reference(
            note_other.id, InsertFormReferenceBlockDTO(form_id=other_form.id)
        )
        NoteService.create(NoteSaveDTO(title="Empty"))

        params = SearchParams(
            filtersCriteria=[
                SearchFilterCriteria(
                    key="form_template_id",
                    operator=SearchOperator.EQ,
                    value=version.template_id,
                )
            ]
        )
        page = NoteService.search(params)
        ids = [n.id for n in page.results]
        self.assertEqual(ids, [note_target.id])

    def test_search_by_form_template_id_no_duplicates_when_multiple_forms_same_template(self):
        # A note embedding two distinct forms from the same template must
        # still appear exactly once in the results (no row multiplication
        # from the join).
        version = self._published_version("Demo")
        form_a = FormService.create(CreateFormDTO(template_version_id=version.id))
        form_b = FormService.create(CreateFormDTO(template_version_id=version.id))

        note = NoteService.create(NoteSaveDTO(title="Two forms"))
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form_a.id)
        )
        NoteService.insert_form_block_reference(
            note.id, InsertFormReferenceBlockDTO(form_id=form_b.id)
        )

        params = SearchParams(
            filtersCriteria=[
                SearchFilterCriteria(
                    key="form_template_id",
                    operator=SearchOperator.EQ,
                    value=version.template_id,
                )
            ]
        )
        page = NoteService.search(params)
        ids = [n.id for n in page.results]
        self.assertEqual(ids, [note.id])

    def _search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = NoteService.search(search_dict).to_dto()
        self.assertEqual(paginator.total_number_of_items, expected_nb_of_result)

    def _published_version(self, template_name: str) -> FormTemplateVersion:
        template = FormTemplateService.create(CreateFormTemplateDTO(name=template_name))
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

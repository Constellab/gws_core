from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import FormStatus
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    UpdateFormTemplateDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigin
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.test.base_test_case import BaseTestCase


# test_form_template_crud
class TestFormTemplateCrud(BaseTestCase):
    def test_create_auto_creates_draft_v0(self):
        template = FormTemplateService.create(
            CreateFormTemplateDTO(name="My form", description="A demo")
        )
        self.assertIsInstance(template, FormTemplate)
        self.assertEqual(template.name, "My form")
        self.assertEqual(template.description, "A demo")
        self.assertFalse(template.is_archived)

        drafts = list(
            FormTemplateVersion.select().where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
        )
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].version, 0)

    def test_get_full_returns_versions(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        full = FormTemplateService.get_full(template.id)
        self.assertEqual(full.name, "X")
        self.assertEqual(len(full.versions), 1)
        self.assertEqual(full.versions[0].status, FormTemplateVersionStatus.DRAFT)

    def test_update_name_and_description(self):
        template = FormTemplateService.create(
            CreateFormTemplateDTO(name="Old name", description="old desc")
        )
        updated = FormTemplateService.update(
            template.id,
            UpdateFormTemplateDTO(name="New name", description="new desc"),
        )
        self.assertEqual(updated.name, "New name")
        self.assertEqual(updated.description, "new desc")

    def test_archive_then_unarchive(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))

        archived = FormTemplateService.archive(template.id)
        self.assertTrue(archived.is_archived)

        # double-archive raises
        with self.assertRaises(BadRequestException):
            FormTemplateService.archive(template.id)

        unarchived = FormTemplateService.unarchive(template.id)
        self.assertFalse(unarchived.is_archived)

        # double-unarchive raises
        with self.assertRaises(BadRequestException):
            FormTemplateService.unarchive(template.id)

    def test_hard_delete_no_forms_succeeds(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        template_id = template.id

        FormTemplateService.hard_delete(template_id)

        self.assertIsNone(FormTemplate.get_by_id(template_id))

    def test_hard_delete_unaffected_by_archive(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        FormTemplateService.archive(template.id)
        FormTemplateService.hard_delete(template.id)
        self.assertIsNone(FormTemplate.get_by_id(template.id))

    def test_hard_delete_rejected_when_form_references_a_version(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        # publish the draft so we can attach a Form
        draft = self._get_draft(template)
        # write a minimal valid spec into the draft, then publish
        spec = ConfigSpecs({"name": StrParam(human_name="Name")}).to_dto()
        draft.content = {k: v.to_json_dict() for k, v in spec.items()}
        draft.save()
        published = FormTemplateService.publish_version(template.id, draft.id)

        # create a Form via the model directly (Phase 3 service doesn't exist yet)
        form = Form()
        form.name = "f"
        form.template_version = published
        form.status = FormStatus.DRAFT
        form.values = {}
        form.save()

        with self.assertRaises(BadRequestException):
            FormTemplateService.hard_delete(template.id)

    def test_search_by_name_returns_template(self):
        a = FormTemplateService.create(CreateFormTemplateDTO(name="alpha"))
        FormTemplateService.create(CreateFormTemplateDTO(name="beta"))

        params = SearchParams(
            filtersCriteria=[{"key": "name", "operator": "CONTAINS", "value": "alph"}]
        )
        page = FormTemplateService.search(params)
        ids = [t.id for t in page.results]
        self.assertIn(a.id, ids)

    def test_search_by_tag_returns_template(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))

        EntityTagList.find_by_entity(
            TagEntityType.FORM_TEMPLATE,
            template.id,
            default_origin=TagOrigin.current_user_origin(),
        ).add_tags([Tag("env", "prod")])

        params = SearchParams(
            filtersCriteria=[
                {"key": "tags", "operator": "EQ", "value": [{"key": "env", "value": "prod"}]}
            ]
        )
        page = FormTemplateService.search(params)
        ids = [t.id for t in page.results]
        self.assertIn(template.id, ids)

    # --- helpers ----------------------------------------------------------

    def _get_draft(self, template: FormTemplate) -> FormTemplateVersion:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )

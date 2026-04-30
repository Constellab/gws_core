from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import FormStatus
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateDraftVersionDTO,
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    UpdateDraftVersionDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict(spec_keys: list[str]) -> dict:
    """Helper: build a serialized ConfigSpecs dict with one StrParam per key."""
    specs = ConfigSpecs(
        {k: StrParam(human_name=k) for k in spec_keys}
    ).to_dto()
    return {k: v.to_json_dict() for k, v in specs.items()}


# test_form_template_versioning
class TestFormTemplateVersioning(BaseTestCase):

    def test_create_draft_rejected_when_one_exists(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))

        with self.assertRaises(BadRequestException):
            FormTemplateService.create_draft(template.id, CreateDraftVersionDTO())

    def test_create_draft_copies_content(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_spec_dict(["a"]))
        )
        published = FormTemplateService.publish_version(template.id, draft.id)

        new_draft = FormTemplateService.create_draft(
            template.id, CreateDraftVersionDTO(copy_from_version_id=published.id)
        )
        self.assertEqual(new_draft.content, published.content)
        self.assertEqual(new_draft.status, FormTemplateVersionStatus.DRAFT)
        self.assertEqual(new_draft.version, 0)

    def test_update_draft_mutates_content(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        new_content = _spec_dict(["foo"])
        updated = FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=new_content)
        )
        self.assertEqual(updated.content, new_content)

    def test_update_rejected_on_non_draft(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_spec_dict(["a"]))
        )
        published = FormTemplateService.publish_version(template.id, draft.id)

        with self.assertRaises(BadRequestException):
            FormTemplateService.update_draft(
                template.id, published.id, UpdateDraftVersionDTO(content=_spec_dict(["b"]))
            )

    def test_publish_assigns_incrementing_versions(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id, draft.id, UpdateDraftVersionDTO(content=_spec_dict(["a"]))
        )
        v1 = FormTemplateService.publish_version(template.id, draft.id)
        self.assertEqual(v1.status, FormTemplateVersionStatus.PUBLISHED)
        self.assertEqual(v1.version, 1)
        self.assertIsNotNone(v1.published_at)
        self.assertIsNotNone(v1.published_by)

        # second draft → second publish
        draft_2 = FormTemplateService.create_draft(template.id, CreateDraftVersionDTO())
        FormTemplateService.update_draft(
            template.id, draft_2.id, UpdateDraftVersionDTO(content=_spec_dict(["b"]))
        )
        v2 = FormTemplateService.publish_version(template.id, draft_2.id)
        self.assertEqual(v2.version, 2)

    def test_publish_rejected_on_non_draft(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        published = FormTemplateService.publish_version(template.id, draft.id)

        with self.assertRaises(BadRequestException):
            FormTemplateService.publish_version(template.id, published.id)

    def test_publish_rejects_invalid_schema(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        # Garbage content that isn't a valid serialized ConfigSpecs.
        draft.content = {"oops": {"not": "a real param spec"}}
        draft.save()

        with self.assertRaises(BadRequestException):
            FormTemplateService.publish_version(template.id, draft.id)

    def test_new_draft_allowed_after_publish(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        FormTemplateService.publish_version(template.id, draft.id)

        new_draft = FormTemplateService.create_draft(
            template.id, CreateDraftVersionDTO()
        )
        self.assertEqual(new_draft.status, FormTemplateVersionStatus.DRAFT)

    def test_archive_version_only_on_published(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)

        # archive on DRAFT raises
        with self.assertRaises(BadRequestException):
            FormTemplateService.archive_version(template.id, draft.id)

        published = FormTemplateService.publish_version(template.id, draft.id)
        archived = FormTemplateService.archive_version(template.id, published.id)
        self.assertEqual(archived.status, FormTemplateVersionStatus.ARCHIVED)

        # archive on already-archived raises
        with self.assertRaises(BadRequestException):
            FormTemplateService.archive_version(template.id, archived.id)

    def test_delete_draft_succeeds(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        FormTemplateService.delete_version(template.id, draft.id)
        self.assertIsNone(FormTemplateVersion.get_by_id(draft.id))

    def test_delete_published_rejected(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        published = FormTemplateService.publish_version(template.id, draft.id)
        with self.assertRaises(BadRequestException):
            FormTemplateService.delete_version(template.id, published.id)

    def test_delete_archived_without_refs_succeeds(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        published = FormTemplateService.publish_version(template.id, draft.id)
        archived = FormTemplateService.archive_version(template.id, published.id)
        FormTemplateService.delete_version(template.id, archived.id)
        self.assertIsNone(FormTemplateVersion.get_by_id(archived.id))

    def test_delete_archived_with_refs_rejected(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = self._get_draft(template)
        published = FormTemplateService.publish_version(template.id, draft.id)

        form = Form()
        form.name = "f"
        form.template_version = published
        form.status = FormStatus.DRAFT
        form.values = {}
        form.save()

        archived = FormTemplateService.archive_version(template.id, published.id)
        with self.assertRaises(BadRequestException):
            FormTemplateService.delete_version(template.id, archived.id)

    def test_get_version_rejects_mismatched_template(self):
        template_a = FormTemplateService.create(CreateFormTemplateDTO(name="A"))
        template_b = FormTemplateService.create(CreateFormTemplateDTO(name="B"))
        draft_a = self._get_draft(template_a)

        with self.assertRaises(BadRequestException):
            FormTemplateService.get_version(template_b.id, draft_a.id)

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

"""CRUD-flavored tests for Form: create, update, archive, hard-delete,
tag propagation at create time, and search.

Save flow / submit / events live in test_form_save_and_submit.py and
test_form_save_events.py.
"""
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_dto import (
    CreateFormDTO,
    FormStatus,
    UpdateFormDTO,
)
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    UpdateDraftVersionDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigin
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict_with_str(*keys: str) -> dict:
    spec = ConfigSpecs({k: StrParam(human_name=k, optional=True) for k in keys}).to_dto()
    return {k: v.to_json_dict() for k, v in spec.items()}


class TestFormCrud(BaseTestCase):
    # ------------------------------------------------------------------ #
    # create
    # ------------------------------------------------------------------ #

    def test_create_from_published_version(self):
        version = self._published_version("Demo")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))
        self.assertIsInstance(form, Form)
        self.assertEqual(form.status, FormStatus.DRAFT)
        self.assertEqual(form.name, "Demo")
        self.assertFalse(form.is_archived)
        self.assertIsNone(form.values)

    def test_create_with_explicit_name_overrides_default(self):
        version = self._published_version("Default")
        form = FormService.create(
            CreateFormDTO(template_version_id=version.id, name="Custom")
        )
        self.assertEqual(form.name, "Custom")

    def test_create_from_draft_version_rejected(self):
        template = FormTemplateService.create(CreateFormTemplateDTO(name="T"))
        draft = self._get_draft(template)
        with self.assertRaises(BadRequestException):
            FormService.create(CreateFormDTO(template_version_id=draft.id))

    def test_create_from_archived_version_rejected(self):
        version = self._published_version("T")
        archived = FormTemplateService.archive_version(version.template_id, version.id)
        with self.assertRaises(BadRequestException):
            FormService.create(CreateFormDTO(template_version_id=archived.id))

    def test_create_copies_propagable_tags_from_template(self):
        version = self._published_version("T")
        template_id = version.template_id

        EntityTagList.find_by_entity(
            TagEntityType.FORM_TEMPLATE,
            template_id,
            default_origin=TagOrigin.current_user_origin(),
        ).add_tags(
            [
                Tag("env", "prod", is_propagable=True),
                Tag("private", "yes"),  # not propagable — should not copy
            ]
        )

        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
        keys = {t.tag_key for t in form_tags.get_tags()}
        self.assertIn("env", keys)
        self.assertNotIn("private", keys)

    # ------------------------------------------------------------------ #
    # update / archive / unarchive
    # ------------------------------------------------------------------ #

    def test_update_name(self):
        form = self._make_form()
        updated = FormService.update(form.id, UpdateFormDTO(name="Renamed"))
        self.assertEqual(updated.name, "Renamed")

    def test_archive_then_unarchive(self):
        form = self._make_form()
        archived = FormService.archive(form.id)
        self.assertTrue(archived.is_archived)
        with self.assertRaises(BadRequestException):
            FormService.archive(form.id)

        unarchived = FormService.unarchive(form.id)
        self.assertFalse(unarchived.is_archived)
        with self.assertRaises(BadRequestException):
            FormService.unarchive(form.id)

    # ------------------------------------------------------------------ #
    # hard delete
    # ------------------------------------------------------------------ #

    def test_hard_delete_cascades_to_save_events(self):
        form = self._make_form()

        # Insert two save events directly so we don't need the full save flow here.
        e1 = FormSaveEvent()
        e1.form = form
        e1.user = form.created_by
        e1.set_changes([])
        e1.save()
        e2 = FormSaveEvent()
        e2.form = form
        e2.user = form.created_by
        e2.set_changes([])
        e2.save()

        FormService.hard_delete(form.id)

        self.assertIsNone(Form.get_by_id(form.id))
        remaining = list(FormSaveEvent.select().where(FormSaveEvent.form == form.id))
        self.assertEqual(remaining, [])

    def test_hard_delete_phase_3_no_op_guard_allows(self):
        # Phase 6 will reject delete when a Note references the form via a
        # FORM block. Phase 3 has no FORM block type, so the guard is a stub.
        form = self._make_form()
        FormService.hard_delete(form.id)
        self.assertIsNone(Form.get_by_id(form.id))

    # ------------------------------------------------------------------ #
    # search
    # ------------------------------------------------------------------ #

    def test_search_by_status(self):
        form = self._make_form()
        params = SearchParams(
            filtersCriteria=[
                {"key": "status", "operator": "EQ", "value": FormStatus.DRAFT.value}
            ]
        )
        page = FormService.search(params)
        ids = [f.id for f in page.results]
        self.assertIn(form.id, ids)

    def test_search_by_template_id(self):
        version = self._published_version("Demo")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))
        # second template, second form
        other = self._published_version("Other")
        FormService.create(CreateFormDTO(template_version_id=other.id))

        params = SearchParams(
            filtersCriteria=[
                {"key": "template_id", "operator": "EQ", "value": version.template_id}
            ]
        )
        page = FormService.search(params)
        ids = [f.id for f in page.results]
        self.assertIn(form.id, ids)
        self.assertEqual(len(ids), 1)

    def test_search_by_name(self):
        form = self._make_form(name="findable")
        self._make_form(name="other")
        params = SearchParams(
            filtersCriteria=[{"key": "name", "operator": "CONTAINS", "value": "find"}]
        )
        page = FormService.search(params)
        ids = [f.id for f in page.results]
        self.assertIn(form.id, ids)

    def test_search_by_tag(self):
        form = self._make_form()
        EntityTagList.find_by_entity(
            TagEntityType.FORM,
            form.id,
            default_origin=TagOrigin.current_user_origin(),
        ).add_tags([Tag("env", "qa")])

        params = SearchParams(
            filtersCriteria=[
                {
                    "key": "tags",
                    "operator": "EQ",
                    "value": [{"key": "env", "value": "qa"}],
                }
            ]
        )
        page = FormService.search(params)
        ids = [f.id for f in page.results]
        self.assertIn(form.id, ids)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _published_version(self, template_name: str) -> FormTemplateVersion:
        template = FormTemplateService.create(CreateFormTemplateDTO(name=template_name))
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id,
            draft.id,
            UpdateDraftVersionDTO(content=_spec_dict_with_str("name")),
        )
        return FormTemplateService.publish_version(template.id, draft.id)

    def _get_draft(self, template) -> FormTemplateVersion:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )

    def _make_form(self, name: str | None = None) -> Form:
        version = self._published_version(name or "Demo")
        return FormService.create(
            CreateFormDTO(template_version_id=version.id, name=name)
        )

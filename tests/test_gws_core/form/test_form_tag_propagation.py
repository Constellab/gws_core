"""Tag propagation FormTemplate -> Form (Phase 4).

Initial tag copy at form creation is covered in test_form_crud.py. This file
covers ongoing propagation: adding/removing a propagable tag on a template
after forms exist must reach (or unreach) every form bound to the template.
"""

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.entity_navigator.entity_navigator import (
    EntityNavigator,
    EntityNavigatorForm,
    EntityNavigatorFormTemplate,
)
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType
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
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigin, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_service import TagService
from gws_core.test.base_test_case import BaseTestCase


def _spec_dict_with_str(*keys: str) -> dict:
    spec = ConfigSpecs({k: StrParam(human_name=k, optional=True) for k in keys}).to_dto()
    return {k: v.to_json_dict() for k, v in spec.items()}


class TestFormTagPropagation(BaseTestCase):
    # ------------------------------------------------------------------ #
    # propagate add
    # ------------------------------------------------------------------ #

    def test_propagable_tag_on_template_reaches_existing_forms(self):
        version = self._published_version("T")
        template_id = version.template_id
        form1 = FormService.create(CreateFormDTO(template_version_id=version.id))
        form2 = FormService.create(CreateFormDTO(template_version_id=version.id))

        tag = Tag(
            "env",
            "prod",
            is_propagable=True,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(TagEntityType.FORM_TEMPLATE, template_id, [tag])

        for form_id in (form1.id, form2.id):
            tags = EntityTagList.find_by_entity(TagEntityType.FORM, form_id)
            entity_tag = tags.get_tag(tag)
            self.assertIsNotNone(entity_tag, f"tag missing on form {form_id}")
            simple = entity_tag.to_simple_tag()
            self.assertTrue(
                simple.origins.has_origin(TagOriginType.FORM_TEMPLATE_PROPAGATED, template_id)
            )

    def test_non_propagable_tag_on_template_does_not_reach_forms(self):
        version = self._published_version("T")
        template_id = version.template_id
        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        tag = Tag(
            "private",
            "yes",
            is_propagable=False,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(TagEntityType.FORM_TEMPLATE, template_id, [tag])

        template_tags = EntityTagList.find_by_entity(TagEntityType.FORM_TEMPLATE, template_id)
        self.assertTrue(template_tags.has_tag(tag))

        form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
        self.assertFalse(form_tags.has_tag(tag))

    # ------------------------------------------------------------------ #
    # propagate delete
    # ------------------------------------------------------------------ #

    def test_remove_propagable_tag_from_template_removes_from_forms(self):
        version = self._published_version("T")
        template_id = version.template_id
        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        tag = Tag(
            "env",
            "prod",
            is_propagable=True,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(TagEntityType.FORM_TEMPLATE, template_id, [tag])

        # sanity: propagated
        self.assertTrue(EntityTagList.find_by_entity(TagEntityType.FORM, form.id).has_tag(tag))

        TagService.delete_tag_from_entity(
            TagEntityType.FORM_TEMPLATE, template_id, tag.key, tag.value
        )

        self.assertFalse(
            EntityTagList.find_by_entity(TagEntityType.FORM_TEMPLATE, template_id).has_tag(tag)
        )
        self.assertFalse(EntityTagList.find_by_entity(TagEntityType.FORM, form.id).has_tag(tag))

    def test_user_added_form_tag_survives_template_tag_removal(self):
        # Form does NOT support multiple origins per tag (only Note does --
        # see EntityTagList.support_multiple_origins). So "user re-adds the
        # same propagated tag" collapses to a single EntityTag. The
        # user-protection semantics that matter on a Form are: a *different*
        # user tag is unaffected when the propagated one is removed.
        version = self._published_version("T")
        template_id = version.template_id
        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        propagated = Tag(
            "env",
            "prod",
            is_propagable=True,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(
            TagEntityType.FORM_TEMPLATE, template_id, [propagated]
        )

        user_only = Tag(
            "owner",
            "alice",
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tag_to_entity(TagEntityType.FORM, form.id, user_only)

        TagService.delete_tag_from_entity(
            TagEntityType.FORM_TEMPLATE, template_id, propagated.key, propagated.value
        )

        form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
        # Propagated tag is gone.
        self.assertFalse(form_tags.has_tag(propagated))
        # User-added unrelated tag survives.
        self.assertTrue(form_tags.has_tag(user_only))

    def test_propagation_across_multiple_versions(self):
        # Two published versions of the same template; one form on each.
        template = FormTemplateService.create(CreateFormTemplateDTO(name="T"))
        v1 = self._publish_draft(template)
        v2 = self._add_and_publish_new_version(template)

        form_v1 = FormService.create(CreateFormDTO(template_version_id=v1.id))
        form_v2 = FormService.create(CreateFormDTO(template_version_id=v2.id))

        tag = Tag(
            "env",
            "prod",
            is_propagable=True,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(TagEntityType.FORM_TEMPLATE, template.id, [tag])

        for form_id in (form_v1.id, form_v2.id):
            self.assertTrue(
                EntityTagList.find_by_entity(TagEntityType.FORM, form_id).has_tag(tag),
                f"form {form_id} missing propagated tag",
            )

    # ------------------------------------------------------------------ #
    # initial copy untouched
    # ------------------------------------------------------------------ #

    def test_initial_copy_at_form_creation_unchanged(self):
        # Tag the template first, then create a form. Phase 3 path must keep
        # working after the new wiring lands.
        version = self._published_version("T")
        template_id = version.template_id

        EntityTagList.find_by_entity(
            TagEntityType.FORM_TEMPLATE,
            template_id,
            default_origin=TagOrigin.current_user_origin(),
        ).add_tags([Tag("env", "prod", is_propagable=True)])

        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
        keys = {t.tag_key for t in form_tags.get_tags()}
        self.assertIn("env", keys)

    # ------------------------------------------------------------------ #
    # leaf + factory
    # ------------------------------------------------------------------ #

    def test_form_is_leaf_no_further_propagation(self):
        version = self._published_version("T")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        # Sanity: tagging a form directly with propagation should no-op
        # downstream and should not crash.
        tag = Tag(
            "env",
            "qa",
            is_propagable=True,
            origins=TagOrigins(TagOriginType.USER, "user_id"),
        )
        TagService.add_tags_to_entity_and_propagate(TagEntityType.FORM, form.id, [tag])

        form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
        self.assertTrue(form_tags.has_tag(tag))

    def test_from_entity_id_form_template_and_form(self):
        version = self._published_version("T")
        form = FormService.create(CreateFormDTO(template_version_id=version.id))

        nav_t = EntityNavigator.from_entity_id(
            NavigableEntityType.FORM_TEMPLATE, version.template_id
        )
        self.assertIsInstance(nav_t, EntityNavigatorFormTemplate)

        nav_f = EntityNavigator.from_entity_id(NavigableEntityType.FORM, form.id)
        self.assertIsInstance(nav_f, EntityNavigatorForm)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _published_version(self, template_name: str) -> FormTemplateVersion:
        template = FormTemplateService.create(CreateFormTemplateDTO(name=template_name))
        return self._publish_draft(template)

    def _publish_draft(self, template) -> FormTemplateVersion:
        draft = self._get_draft(template)
        FormTemplateService.update_draft(
            template.id,
            draft.id,
            UpdateDraftVersionDTO(content=_spec_dict_with_str("name")),
        )
        return FormTemplateService.publish_version(template.id, draft.id)

    def _add_and_publish_new_version(self, template) -> FormTemplateVersion:
        draft = FormTemplateService.create_draft(template.id)
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

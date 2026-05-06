from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.form.form import Form
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateDraftVersionDTO,
    CreateFormTemplateDTO,
    FormTemplateFullDTO,
    FormTemplateVersionStatus,
    UpdateDraftVersionDTO,
    UpdateFormTemplateDTO,
)
from gws_core.form_template.form_template_search_builder import (
    FormTemplateSearchBuilder,
)
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note_template.note_template_form_template_model import (
    NoteTemplateFormTemplateModel,
)
from gws_core.user.activity.activity_dto import ActivityObjectType, ActivityType
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.current_user_service import CurrentUserService


class FormTemplateService:
    # ------------------------------------------------------------------ #
    # Template-level CRUD
    # ------------------------------------------------------------------ #

    @classmethod
    @GwsCoreDbManager.transaction()
    def create(cls, dto: CreateFormTemplateDTO) -> FormTemplate:
        """Create a FormTemplate and auto-create its DRAFT v=0 with empty content."""
        template = FormTemplate()
        template.name = dto.name
        template.description = dto.description
        template.save()

        draft = FormTemplateVersion()
        draft.template = template
        draft.status = FormTemplateVersionStatus.DRAFT
        draft.version = 1
        draft.content = None
        draft.save()

        ActivityService.add(
            ActivityType.CREATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template.id,
        )
        return template

    @classmethod
    def get_by_id_and_check(cls, template_id: str) -> FormTemplate:
        return FormTemplate.get_by_id_and_check(template_id)

    @classmethod
    def get_full(cls, template_id: str) -> FormTemplateFullDTO:
        template = cls.get_by_id_and_check(template_id)
        return template.to_full_dto()

    @classmethod
    @GwsCoreDbManager.transaction()
    def update(cls, template_id: str, dto: UpdateFormTemplateDTO) -> FormTemplate:
        template = cls.get_by_id_and_check(template_id)
        if dto.name is not None:
            template.name = dto.name
        if dto.description is not None:
            template.description = dto.description
        template.save()

        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return template

    @classmethod
    @GwsCoreDbManager.transaction()
    def archive(cls, template_id: str) -> FormTemplate:
        template = cls.get_by_id_and_check(template_id)
        if template.is_archived:
            raise BadRequestException("The form template is already archived")
        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return template.archive(True)

    @classmethod
    @GwsCoreDbManager.transaction()
    def unarchive(cls, template_id: str) -> FormTemplate:
        template = cls.get_by_id_and_check(template_id)
        if not template.is_archived:
            raise BadRequestException("The form template is not archived")
        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return template.archive(False)

    @classmethod
    @GwsCoreDbManager.transaction()
    def hard_delete(cls, template_id: str) -> None:
        template = cls.get_by_id_and_check(template_id)

        form_count = Form.count_for_template(template.id)
        if form_count > 0:
            raise BadRequestException(
                f"Cannot delete form template: {form_count} form(s) reference it. Archive instead."
            )

        # Spec §5.6 dual: any NoteTemplate that still pins a version of this
        # template family blocks the delete (RESTRICT FK on the join would
        # also catch it, but a friendly error is nicer).
        note_template_ref_count = (
            NoteTemplateFormTemplateModel.get_by_form_template(template.id).count()
        )
        if note_template_ref_count > 0:
            raise BadRequestException(
                f"Cannot delete form template: {note_template_ref_count} "
                "note template(s) still embed a version of it. Remove the "
                "FORM_TEMPLATE blocks from those note templates first."
            )

        template.delete_instance()

        ActivityService.add(
            ActivityType.DELETE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #

    @classmethod
    def search(
        cls,
        search: SearchParams,
        page: int = 0,
        number_of_items_per_page: int = 20,
    ) -> Paginator[FormTemplate]:
        search_builder = FormTemplateSearchBuilder()
        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    # ------------------------------------------------------------------ #
    # Version-level lifecycle
    # ------------------------------------------------------------------ #

    @classmethod
    def get_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        version = FormTemplateVersion.get_by_id_and_check(version_id)
        if version.template_id != template_id:
            raise BadRequestException("The version does not belong to the given form template")
        return version

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_draft(
        cls,
        template_id: str,
        dto: CreateDraftVersionDTO | None = None,
    ) -> FormTemplateVersion:
        """Create a new DRAFT version for a template.

        Rejected if a DRAFT already exists. Optionally copies content from a
        prior PUBLISHED or ARCHIVED version (via dto.copy_from_version_id).
        """
        template = cls.get_by_id_and_check(template_id)

        if FormTemplateVersion.has_draft_for_template(template.id):
            raise BadRequestException(
                "A DRAFT version already exists for this form template. "
                "Edit or delete it before creating a new draft."
            )

        content = None
        if dto is not None and dto.copy_from_version_id:
            source = cls.get_version(template_id, dto.copy_from_version_id)
            content = source.content
        else:
            latest_published = FormTemplateVersion.get_current_published_version(template.id)
            if latest_published is not None:
                content = latest_published.content

        max_version = FormTemplateVersion.get_max_published_or_archived_version(template.id)

        draft = FormTemplateVersion()
        draft.template = template
        draft.status = FormTemplateVersionStatus.DRAFT
        draft.version = max_version + 1
        draft.content = content
        draft.save()

        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return draft

    @classmethod
    @GwsCoreDbManager.transaction()
    def update_draft(
        cls,
        template_id: str,
        version_id: str,
        dto: UpdateDraftVersionDTO,
    ) -> FormTemplateVersion:
        version = cls.get_version(template_id, version_id)
        if version.status != FormTemplateVersionStatus.DRAFT:
            raise BadRequestException(
                "Only DRAFT versions can be edited. "
                "Create a new draft to change a published schema."
            )
        version.content = dto.content
        version.save()

        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return version

    @classmethod
    @GwsCoreDbManager.transaction()
    def publish_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        """DRAFT → PUBLISHED.

        Validates schema and sets published_at / published_by. The version
        number was already assigned (max+1) at draft creation.
        """
        version = cls.get_version(template_id, version_id)
        if version.status != FormTemplateVersionStatus.DRAFT:
            raise BadRequestException("Only DRAFT versions can be published.")

        # Schema validation. Empty content is allowed (a form with no fields
        # is valid; from_json({}) gives an empty ConfigSpecs).
        try:
            specs = ConfigSpecs.from_json(version.content or {})
            specs.check_config_specs()
        except Exception as err:
            raise BadRequestException(f"Cannot publish: schema is invalid ({err})") from err

        version.status = FormTemplateVersionStatus.PUBLISHED
        version.published_at = DateHelper.now_utc()
        version.published_by = CurrentUserService.get_and_check_current_user()
        version.save()

        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return version

    @classmethod
    @GwsCoreDbManager.transaction()
    def archive_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        version = cls.get_version(template_id, version_id)
        if version.status != FormTemplateVersionStatus.PUBLISHED:
            raise BadRequestException("Only PUBLISHED versions can be archived.")
        version.status = FormTemplateVersionStatus.ARCHIVED
        version.save()

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return version

    @classmethod
    @GwsCoreDbManager.transaction()
    def unarchive_version(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        version = cls.get_version(template_id, version_id)
        if version.status != FormTemplateVersionStatus.ARCHIVED:
            raise BadRequestException("Only ARCHIVED versions can be unarchived.")
        version.status = FormTemplateVersionStatus.PUBLISHED
        version.save()

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )
        return version

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_version(cls, template_id: str, version_id: str) -> None:
        version = cls.get_version(template_id, version_id)

        if version.status == FormTemplateVersionStatus.PUBLISHED:
            raise BadRequestException("Cannot delete a PUBLISHED version. Archive it first.")

        if version.status == FormTemplateVersionStatus.ARCHIVED:
            form_count = Form.count_for_version(version.id)
            if form_count > 0:
                raise BadRequestException(
                    f"Cannot delete archived version: {form_count} form(s) reference it."
                )
            note_template_ref_count = (
                NoteTemplateFormTemplateModel.count_by_form_template_version(version.id)
            )
            if note_template_ref_count > 0:
                raise BadRequestException(
                    "Cannot delete archived version: "
                    f"{note_template_ref_count} note template(s) still pin "
                    "it via FORM_TEMPLATE blocks."
                )

        version.delete_instance()

        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM_TEMPLATE,
            object_id=template_id,
        )

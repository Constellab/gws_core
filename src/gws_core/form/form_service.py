from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.form.form import Form
from gws_core.form.form_dto import (
    CreateFormDTO,
    FormChangeAction,
    FormChangeEntry,
    FormSaveResultDTO,
    FormStatus,
    SaveFormDTO,
    UpdateFormDTO,
)
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_search_builder import FormSearchBuilder
from gws_core.form_template.form_template_dto import FormTemplateVersionStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.note.note_form_model import NoteFormModel
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.user.activity.activity_dto import ActivityObjectType, ActivityType
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.current_user_service import CurrentUserService

# Reserved field path used in FormChangeEntry for status transitions.
# Underscores guarantee no collision with a real ConfigSpecs key
# (spec keys are validated identifiers).
_STATUS_FIELD_PATH = "__status"


class FormService:
    """CRUD + save flow for Form. See form_feature.md §3.3, §8, §9.2."""

    # ------------------------------------------------------------------ #
    # Create / read
    # ------------------------------------------------------------------ #

    @classmethod
    @GwsCoreDbManager.transaction()
    def create(cls, dto: CreateFormDTO) -> Form:
        """Create a Form from a PUBLISHED FormTemplateVersion.

        Rejects DRAFT and ARCHIVED versions. Default name = the parent
        FormTemplate's name; can be overridden via dto.name.

        Copies propagable tags from the parent FormTemplate to the new
        Form (initial copy at creation time, per spec §3.5). Ongoing
        propagation when a template tag changes after the fact is Phase 4.
        """
        version = FormTemplateVersion.get_by_id_and_check(dto.template_version_id)
        if version.status != FormTemplateVersionStatus.PUBLISHED:
            raise BadRequestException(
                "Can only create a Form from a PUBLISHED template version, "
                f"but this version has status {version.status.value}."
            )

        form = Form()
        form.name = dto.name if dto.name is not None else version.template.name
        form.template_version = version
        form.status = FormStatus.DRAFT
        form.values = None
        form.save()

        # Initial tag copy from parent template (mirrors note_service.py:497-502).
        template_id = version.template_id
        template_tags = EntityTagList.find_by_entity(
            TagEntityType.FORM_TEMPLATE, template_id
        )
        propagated = template_tags.build_tags_propagated(
            TagOriginType.FORM_TEMPLATE_PROPAGATED, template_id
        )
        if propagated:
            form_tags = EntityTagList.find_by_entity(TagEntityType.FORM, form.id)
            form_tags.add_tags(propagated)

        ActivityService.add(
            ActivityType.CREATE,
            object_type=ActivityObjectType.FORM,
            object_id=form.id,
        )
        return form

    @classmethod
    def get_by_id_and_check(cls, form_id: str) -> Form:
        return Form.get_by_id_and_check(form_id)

    @classmethod
    def get_full(cls, form_id: str) -> FormSaveResultDTO:
        """Return the form with its stored values plus per-computed-field
        errors recomputed against the current values.

        Storage is the union (user keys + computed keys) so reads return
        ``form.values`` directly. Recompute is run for the errors dict only
        — values themselves come from storage.
        """
        form = cls.get_by_id_and_check(form_id)
        specs = ConfigSpecs.from_json(form.template_version.content or {})
        # Drive errors only; we don't overwrite stored values on read.
        _, errors = specs.compute_values(form.values or {})
        return FormSaveResultDTO(form=form.to_full_dto(), errors=errors)

    # ------------------------------------------------------------------ #
    # Update / save / submit
    # ------------------------------------------------------------------ #

    @classmethod
    @GwsCoreDbManager.transaction()
    def update(cls, form_id: str, dto: UpdateFormDTO) -> Form:
        """Update name only. Tag changes go through the existing tag
        controller. Allowed in any status."""
        form = cls.get_by_id_and_check(form_id)
        if dto.name is not None:
            form.name = dto.name
        form.save()
        ActivityService.add(
            ActivityType.UPDATE,
            object_type=ActivityObjectType.FORM,
            object_id=form_id,
        )
        return form

    @classmethod
    @GwsCoreDbManager.transaction()
    def save(cls, form_id: str, dto: SaveFormDTO) -> FormSaveResultDTO:
        """Save flow per spec §8.

        DRAFT and SUBMITTED forms can both be saved (re-edit on a SUBMITTED
        form is allowed and stays SUBMITTED — spec §3.3). Type validation
        always runs; missing mandatories only block on transition to
        SUBMITTED. One FormSaveEvent row per save (with the full diff list
        in `changes`); zero rows if nothing changed and no transition.
        """
        form = cls.get_by_id_and_check(form_id)
        specs = ConfigSpecs.from_json(form.template_version.content or {})

        # 3. Strip computed-key submissions then validate. ParamSet.validate
        #    mints/preserves __item_id per row, so the returned dict carries
        #    stable identity ready for diffing and persistence.
        new_values = specs.strip_computed_keys(dto.values or {})
        new_values = specs.validate_values(new_values)

        # 4. Submit gate.
        status_changed = False
        old_status = form.status
        if (
            dto.status_transition == FormStatus.SUBMITTED
            and form.status != FormStatus.SUBMITTED
        ):
            if not specs.mandatory_values_are_set(new_values):
                raise BadRequestException(
                    "Cannot submit: at least one mandatory field is empty."
                )
            form.status = FormStatus.SUBMITTED
            form.submitted_at = DateHelper.now_utc()
            form.submitted_by = CurrentUserService.get_and_check_current_user()
            status_changed = True

        # 5. Compute and merge into the union dict. compute_values mutates
        #    ParamSet rows in place for per-row computed cells; __item_id is
        #    untouched (the evaluator only reads/writes referenced spec keys).
        computed, errors = specs.compute_values(new_values)
        new_values = specs.merge_computed(new_values, computed)

        # 6. Diff and build change list.
        changes = ConfigSpecs.diff_values(form.values or {}, new_values)
        if status_changed:
            changes.append(
                FormChangeEntry(
                    field_path=_STATUS_FIELD_PATH,
                    action=FormChangeAction.STATUS_CHANGED,
                    old_value=old_status.value,
                    new_value=FormStatus.SUBMITTED.value,
                )
            )

        # 8. Persist union.
        form.values = new_values
        if dto.name is not None:
            form.name = dto.name
        form.save()

        # 8b. No-op suppression.
        if changes:
            event = FormSaveEvent()
            event.form = form
            event.user = CurrentUserService.get_and_check_current_user()
            event.set_changes(changes)
            event.save()
            ActivityService.add(
                ActivityType.UPDATE,
                object_type=ActivityObjectType.FORM,
                object_id=form.id,
            )

        return FormSaveResultDTO(form=form.to_full_dto(), errors=errors)

    @classmethod
    @GwsCoreDbManager.transaction()
    def submit(cls, form_id: str) -> FormSaveResultDTO:
        """Sugar for save() with status_transition=SUBMITTED and no value change."""
        form = cls.get_by_id_and_check(form_id)
        return cls.save(
            form_id,
            SaveFormDTO(
                values=form.values or {},
                status_transition=FormStatus.SUBMITTED,
            ),
        )

    # ------------------------------------------------------------------ #
    # Archive / delete
    # ------------------------------------------------------------------ #

    @classmethod
    @GwsCoreDbManager.transaction()
    def archive(cls, form_id: str) -> Form:
        form = cls.get_by_id_and_check(form_id)
        if form.is_archived:
            raise BadRequestException("The form is already archived")
        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.FORM,
            object_id=form_id,
        )
        form.is_archived = True
        form.save()
        return form

    @classmethod
    @GwsCoreDbManager.transaction()
    def unarchive(cls, form_id: str) -> Form:
        form = cls.get_by_id_and_check(form_id)
        if not form.is_archived:
            raise BadRequestException("The form is not archived")
        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.FORM,
            object_id=form_id,
        )
        form.is_archived = False
        form.save()
        return form

    @classmethod
    @GwsCoreDbManager.transaction()
    def hard_delete(cls, form_id: str) -> None:
        """Hard-delete a Form. Cascade-deletes its FormSaveEvent rows via
        the FK on_delete=CASCADE.

        Rejected if any Note still embeds this form via a FORM rich-text
        block (spec §5.6 / §9.2). The DB-level RESTRICT FK on
        NoteFormModel.form is the underlying guarantee; the application
        check produces a friendly error naming up to 5 referencing notes.
        """
        referencing_rows = list(NoteFormModel.get_by_form(form_id))
        if referencing_rows:
            note_titles = [row.note.title for row in referencing_rows[:5]]
            suffix = (
                f" (and {len(referencing_rows) - 5} more)"
                if len(referencing_rows) > 5
                else ""
            )
            raise BadRequestException(
                "Cannot delete form: still referenced by note(s): "
                f"{', '.join(note_titles)}{suffix}. "
                "Remove the form block from these notes first."
            )
        form = cls.get_by_id_and_check(form_id)
        form.delete_instance()
        ActivityService.add(
            ActivityType.DELETE,
            object_type=ActivityObjectType.FORM,
            object_id=form_id,
        )

    # ------------------------------------------------------------------ #
    # Search / history
    # ------------------------------------------------------------------ #

    @classmethod
    def search(
        cls,
        search: SearchParams,
        page: int = 0,
        number_of_items_per_page: int = 20,
    ) -> Paginator[Form]:
        return (
            FormSearchBuilder()
            .add_search_params(search)
            .search_page(page, number_of_items_per_page)
        )

    @classmethod
    def get_history(
        cls,
        form_id: str,
        page: int = 0,
        number_of_items_per_page: int = 20,
    ) -> Paginator[FormSaveEvent]:
        """Paginated FormSaveEvent timeline for a form, ordered created_at DESC."""
        cls.get_by_id_and_check(form_id)
        query = (
            FormSaveEvent.select()
            .where(FormSaveEvent.form == form_id)
            .order_by(FormSaveEvent.created_at.desc())
        )
        return Paginator(query, page, number_of_items_per_page)


from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.computed.computed_param_evaluator import (
    ComputedParamEvaluationError,
    ConfigSpecsEvaluator,
)
from gws_core.config.param.computed.computed_param_graph import (
    ComputedParamGraphChecker,
)
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.form.form import Form
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateDraftVersionDTO,
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    TestFormTemplateVersionDTO,
    TestFormTemplateVersionResultDTO,
    UpdateFormTemplateDTO,
    ValidateComputedParamDTO,
    ValidateComputedParamResultDTO,
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
        note_template_ref_count = NoteTemplateFormTemplateModel.get_by_form_template(
            template.id
        ).count()
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
    def validate_computed_param(
        cls,
        template_id: str,
        version_id: str,
        dto: ValidateComputedParamDTO,
    ) -> ValidateComputedParamResultDTO:
        """Lint a candidate ComputedParam expression against a version's specs.

        The param need not already exist in the version. Returns a result
        rather than raising for expression problems so the editor gets a 200
        with the diagnostic; a missing template/version (or a bad
        ``param_set_key``) still raises.

        :param dto.param_set_key: when set, validates against that ParamSet's
            inner ConfigSpecs (per-row formula). Outer-scope aggregate sugar
            (``@key[].field``) is not allowed in that case; outer references
            via ``@@name`` are allowed and validated against the enclosing
            scope.
        """
        version = cls.get_version(template_id, version_id)
        outer_specs = version.get_content()
        target_specs = cls.resolve_computed_param_scope(outer_specs, dto.param_set_key)
        referenced = sorted(ConfigSpecsEvaluator.extract_referenced_keys(dto.expression))

        error = cls._check_computed_param_expression(dto, target_specs, outer_specs)
        return ValidateComputedParamResultDTO(
            valid=error is None, referenced_keys=referenced, error=error
        )

    @staticmethod
    def resolve_computed_param_scope(
        specs: ConfigSpecs, param_set_key: str | None
    ) -> ConfigSpecs:
        """The ConfigSpecs a computed param would be evaluated in: the version's
        outer specs, or the inner specs of ``param_set_key`` when nesting."""
        if param_set_key is None:
            return specs
        if not specs.has_spec(param_set_key):
            raise BadRequestException(
                f"No field named '{param_set_key}' in this form template version."
            )
        param_set_spec = specs.get_spec(param_set_key)
        if not isinstance(param_set_spec, ParamSet) or param_set_spec.param_set is None:
            raise BadRequestException(
                f"Field '{param_set_key}' is not a ParamSet; "
                "computed params can only be nested inside a ParamSet."
            )
        return param_set_spec.param_set

    @staticmethod
    def _check_computed_param_expression(
        dto: ValidateComputedParamDTO,
        target_specs: ConfigSpecs,
        outer_specs: ConfigSpecs,
    ) -> str | None:
        """Run all expression checks; return None when valid, else the message.

        ``target_specs`` is the scope the candidate would live in (the version
        outer specs, or a ParamSet's inner specs). ``outer_specs`` is always
        the version's top-level specs — same as ``target_specs`` for an outer
        param, the enclosing scope for an inner one. Used to validate `@@name`
        references and to detect cross-scope cycles via the graph checker.
        """
        try:
            candidate = ComputedParam(expression=dto.expression)
        except BadRequestException as err:
            return str(err)

        if dto.param_set_key is not None and ConfigSpecsEvaluator.referenced_paramset_keys(
            dto.expression
        ):
            return (
                "ParamSet aggregate sugar ('@key[].field') is only valid at the "
                "scope containing the ParamSet, not inside a ParamSet row."
            )

        if dto.param_set_key is None and ConfigSpecsEvaluator.extract_referenced_outer_keys(
            dto.expression
        ):
            return (
                "Outer references ('@@name') are only valid inside a ParamSet, "
                "not at the top scope."
            )

        try:
            ConfigSpecsEvaluator.check_expression_syntax(dto.expression)
        except ComputedParamEvaluationError as err:
            return str(err)

        # Reference + cycle checks: build a throwaway ConfigSpecs mirroring the
        # version structure with the candidate inserted at the right scope,
        # then reuse ComputedParamGraphChecker. Caller-supplied key when given
        # (so editing an existing computed param's expression catches a cycle
        # through that key); otherwise a synthetic, collision-proof key.
        target_existing = target_specs.get_specs_as_dict()
        probe_key = dto.key
        if probe_key is None:
            probe_key = "__computed_param_probe__"
            while probe_key in target_existing:
                probe_key += "_"

        if dto.param_set_key is None:
            # Candidate lives at the outer scope.
            probe_specs = ConfigSpecs(
                {**target_existing, probe_key: candidate}, _skip_key_validation=True
            )
        else:
            # Candidate lives inside a ParamSet. Build a probe outer ConfigSpecs
            # with that ParamSet's inner specs replaced so cross-scope cycle
            # detection sees the candidate.
            outer_existing = outer_specs.get_specs_as_dict()
            probe_inner = ConfigSpecs(
                {**target_existing, probe_key: candidate}, _skip_key_validation=True
            )
            original_paramset = outer_existing[dto.param_set_key]
            probe_paramset = ParamSet(
                param_set=probe_inner,
                optional=original_paramset.optional,
                visibility=original_paramset.visibility,
                human_name=original_paramset.human_name,
                short_description=original_paramset.short_description,
                max_number_of_occurrences=original_paramset.max_number_of_occurrences,
            )
            probe_specs = ConfigSpecs(
                {**outer_existing, dto.param_set_key: probe_paramset},
                _skip_key_validation=True,
            )
        try:
            ComputedParamGraphChecker.check(probe_specs)
        except BadRequestException as err:
            # When a synthetic key was used, hide it from the message.
            message = str(err)
            if dto.key is None:
                message = message.replace(probe_key, "<this param>")
            return message
        return None

    @classmethod
    def test_version(
        cls,
        template_id: str,
        version_id: str,
        dto: TestFormTemplateVersionDTO,
    ) -> TestFormTemplateVersionResultDTO:
        """Validate a set of values against a version's specs without persisting.

        Runs the same validation pipeline as a SUBMITTED-transition save
        (computed keys stripped, type validation, computed-value evaluation,
        mandatory-field check) but does not raise: the submit-gate failures
        are returned alongside the renderable result so the front-end can
        display them. No Form is created, no FormSaveEvent is written, and
        the version may be DRAFT.
        """
        version = cls.get_version(template_id, version_id)
        specs = version.get_content()
        validation = FormService.validate_values_against_specs(specs, dto.values)
        missing_paths = specs.get_missing_mandatory_paths(validation.values)
        errors = [
            *(f"Missing mandatory field: {path}" for path in missing_paths),
            *specs.format_field_errors(validation.validation_errors),
            *specs.format_field_errors(validation.computed_errors),
        ]
        return TestFormTemplateVersionResultDTO(
            result=FormService.build_save_result(
                validation.values, specs, validation.computed_errors
            ),
            errors=errors,
        )

    @classmethod
    def list_versions(cls, template_id: str) -> list[FormTemplateVersion]:
        cls.get_by_id_and_check(template_id)
        return list(
            FormTemplateVersion.select()
            .where(FormTemplateVersion.template_id == template_id)
            .order_by(FormTemplateVersion.version.desc())
        )

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

    # ------------------------------------------------------------------ #
    # Draft field-level edits
    # ------------------------------------------------------------------ #

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_draft_field(
        cls,
        template_id: str,
        version_id: str,
        field_key: str,
        spec_dto: ParamSpecDTO,
    ) -> FormTemplateVersion:
        version = cls._get_draft_version_and_check(template_id, version_id)
        specs = version.get_content()
        specs.add_spec(
            field_key, ParamSpecHelper.create_param_spec_from_dto(spec_dto, validate=True)
        )
        return cls._save_draft_specs(version, specs, template_id)

    @classmethod
    @GwsCoreDbManager.transaction()
    def update_draft_field(
        cls,
        template_id: str,
        version_id: str,
        field_key: str,
        spec_dto: ParamSpecDTO,
    ) -> FormTemplateVersion:
        version = cls._get_draft_version_and_check(template_id, version_id)
        specs = version.get_content()
        specs.update_spec(
            field_key, ParamSpecHelper.create_param_spec_from_dto(spec_dto, validate=True)
        )
        return cls._save_draft_specs(version, specs, template_id)

    @classmethod
    @GwsCoreDbManager.transaction()
    def rename_and_update_draft_field(
        cls,
        template_id: str,
        version_id: str,
        field_key: str,
        new_field_key: str,
        spec_dto: ParamSpecDTO,
    ) -> FormTemplateVersion:
        version = cls._get_draft_version_and_check(template_id, version_id)
        specs = version.get_content()
        specs.check_spec_exists(field_key)
        if new_field_key != field_key and specs.has_spec(new_field_key):
            raise BadRequestException(
                f"A field named '{new_field_key}' already exists in this draft."
            )
        specs.remove_spec(field_key)
        specs.add_spec(
            new_field_key,
            ParamSpecHelper.create_param_spec_from_dto(spec_dto, validate=True),
        )
        return cls._save_draft_specs(version, specs, template_id)

    @classmethod
    @GwsCoreDbManager.transaction()
    def reorder_draft_fields(
        cls,
        template_id: str,
        version_id: str,
        field_keys: list[str],
    ) -> FormTemplateVersion:
        """Reorder the fields of a DRAFT version.

        ``field_keys`` must be the full ordered list of current field keys.
        The set must match exactly — any missing or unknown key (typically
        from a concurrent add/delete) aborts the call so the frontend can
        refetch and retry.
        """
        version = cls._get_draft_version_and_check(template_id, version_id)
        specs = version.get_content()

        current = list(specs.get_specs_as_dict().keys())
        if len(field_keys) != len(set(field_keys)):
            raise BadRequestException("Reorder list contains duplicate field names.")
        if set(field_keys) != set(current):
            missing = sorted(set(current) - set(field_keys))
            unknown = sorted(set(field_keys) - set(current))
            raise BadRequestException(
                "Reorder list does not match the current fields. "
                f"missing={missing}, unknown={unknown}. "
                "Refetch the version and retry."
            )

        reordered = {key: specs.get_spec(key) for key in field_keys}
        specs.specs = reordered
        return cls._save_draft_specs(version, specs, template_id)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_draft_field(
        cls,
        template_id: str,
        version_id: str,
        field_key: str,
    ) -> FormTemplateVersion:
        version = cls._get_draft_version_and_check(template_id, version_id)
        specs = version.get_content()
        specs.remove_spec(field_key)
        return cls._save_draft_specs(version, specs, template_id)

    @classmethod
    def _get_draft_version_and_check(cls, template_id: str, version_id: str) -> FormTemplateVersion:
        version = cls.get_version(template_id, version_id)
        if version.status != FormTemplateVersionStatus.DRAFT:
            raise BadRequestException(
                "Only DRAFT versions can be edited. "
                "Create a new draft to change a published schema."
            )
        return version

    @classmethod
    def _save_draft_specs(
        cls,
        version: FormTemplateVersion,
        specs: ConfigSpecs,
        template_id: str,
    ) -> FormTemplateVersion:
        version.update_specs(specs)

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
            specs = version.get_content()
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
            note_template_ref_count = NoteTemplateFormTemplateModel.count_by_form_template_version(
                version.id
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

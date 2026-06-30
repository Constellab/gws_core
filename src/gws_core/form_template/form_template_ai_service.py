
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.config_specs_ai_service import ConfigSpecsAiService
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.form_template.form_template_dto import (
    GenerateComputedParamDTO,
    GenerateComputedParamResultDTO,
    GenerateTemplateFieldDTO,
    GenerateTemplateFieldResultDTO,
    GenerateTemplateSpecsDTO,
    GenerateTemplateSpecsResultDTO,
    ValidateComputedParamDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService


class FormTemplateAiService:
    """AI adapters for form-template editing, over :class:`ConfigSpecsAiService`.

    Holds the form-template concerns — resolving / requiring a DRAFT version,
    building the wire DTOs, and the ComputedParam scope + validation — while the
    generic AI work (prompts, type catalog, GPT call) lives in
    :class:`ConfigSpecsAiService`.

    Nothing here persists: each method returns a preview the editor reviews and
    then applies through the regular field / override-specs routes.
    """

    @classmethod
    def generate_computed_param_expression(
        cls,
        template_id: str,
        version_id: str,
        dto: GenerateComputedParamDTO,
    ) -> GenerateComputedParamResultDTO:
        """Generate a ComputedParam expression from a natural-language description.

        Does not persist anything. The AI call is delegated to
        :meth:`ConfigSpecsAiService.generate_computed_expression`; the returned
        ``expression`` is then run through
        :meth:`FormTemplateService.validate_computed_param` so the front-end can
        surface the suggestion together with any error.
        """
        version = FormTemplateService.get_version(template_id, version_id)
        outer_specs = version.get_content()
        target_specs = FormTemplateService.resolve_computed_param_scope(
            outer_specs, dto.param_set_key
        )

        expression = ConfigSpecsAiService.generate_computed_expression(
            target_specs, outer_specs, dto.description, dto.param_set_key
        )
        validation = FormTemplateService.validate_computed_param(
            template_id,
            version_id,
            ValidateComputedParamDTO(
                expression=expression,
                param_set_key=dto.param_set_key,
                key=None,
            ),
        )
        return GenerateComputedParamResultDTO(expression=expression, validation=validation)

    # ------------------------------------------------------------------ #
    # Template specs / field generation (thin adapters over ConfigSpecsAiService)
    # ------------------------------------------------------------------ #

    @classmethod
    def generate_template_specs(
        cls,
        template_id: str,
        version_id: str,
        dto: GenerateTemplateSpecsDTO,
    ) -> GenerateTemplateSpecsResultDTO:
        """Generate or edit a DRAFT form template's fields from a description.

        Delegates the AI work to :class:`ConfigSpecsAiService` and returns the
        validated proposed specs **without persisting** — the editor reviews
        them and applies them via the override-specs route
        (:meth:`FormTemplateService.override_specs`).

        Only DRAFT versions are accepted (a published schema cannot be edited).
        Raises on an empty description, a JSON-parse failure, or a proposal that
        fails schema validation.
        """
        version = FormTemplateService._get_draft_version_and_check(template_id, version_id)
        specs = ConfigSpecsAiService.generate_specs(
            version.get_content(), dto.description,
            FormTemplateService.ALLOWED_SPEC_CATEGORIES,
        )
        return GenerateTemplateSpecsResultDTO(specs=specs.to_dto())

    @classmethod
    def generate_template_field(
        cls,
        template_id: str,
        version_id: str,
        dto: GenerateTemplateFieldDTO,
    ) -> GenerateTemplateFieldResultDTO:
        """Generate or edit a SINGLE field from a natural-language description.

        Does NOT persist — returns the proposed ``field_key`` + ``spec`` for the
        editor to apply through the existing create/update field routes. The
        draft's other fields are passed as read-only context; ``dto.current_field``
        (when given) is the field's current spec the AI starts from for an edit.

        Only DRAFT versions are accepted. Raises on an empty description, a
        JSON-parse failure, or a field the deserializer/validator rejects.
        """
        version = FormTemplateService._get_draft_version_and_check(template_id, version_id)
        other_specs = cls._other_specs(version.get_content(), dto.field_key)
        current_field = (
            ParamSpecHelper.create_param_spec_from_dto(dto.current_field)
            if dto.current_field is not None
            else None
        )
        field_key, spec = ConfigSpecsAiService.generate_field(
            other_specs, dto.description, dto.field_key, current_field,
            FormTemplateService.ALLOWED_SPEC_CATEGORIES,
        )
        return GenerateTemplateFieldResultDTO(field_key=field_key, spec=spec.to_dto())

    @staticmethod
    def _other_specs(specs: ConfigSpecs, field_key: str | None) -> ConfigSpecs:
        """The version's specs minus the field being edited — the sibling
        context handed to the AI (so it doesn't treat the edited field as a
        sibling to avoid)."""
        return ConfigSpecs(
            {
                key: value
                for key, value in specs.get_specs_as_dict().items()
                if key != field_key
            },
            _skip_key_validation=True,
        )

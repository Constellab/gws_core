from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    ValidateComputedParamDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase


# test_form_template_computed_param_validate
class TestFormTemplateComputedParamValidate(BaseTestCase):
    def _new_template_with_specs(self, specs: ConfigSpecs) -> tuple[FormTemplate, str]:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        draft = (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )
        draft.update_specs(specs)
        return template, draft.id

    def _validate(
        self,
        template: FormTemplate,
        version_id: str,
        expression: str,
        result_type: str = "float",
        param_set_key: str | None = None,
        key: str | None = None,
    ):
        return FormTemplateService.validate_computed_param(
            template.id,
            version_id,
            ValidateComputedParamDTO(
                expression=expression,
                result_type=result_type,
                param_set_key=param_set_key,
                key=key,
            ),
        )

    def test_valid_expression(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"mass": FloatParam(), "volume": FloatParam()})
        )
        result = self._validate(template, version_id, "@mass / @volume")
        self.assertTrue(result.valid)
        self.assertEqual(sorted(result.referenced_keys), ["mass", "volume"])
        self.assertIsNone(result.error)

    def test_unknown_reference(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"mass": FloatParam()})
        )
        result = self._validate(template, version_id, "@mass / @volume")
        self.assertFalse(result.valid)
        self.assertIn("volume", result.error)

    def test_self_cycle_when_editing_existing_computed(self):
        # Editing computed `density`'s expression to reference itself.
        template, version_id = self._new_template_with_specs(
            ConfigSpecs(
                {
                    "mass": FloatParam(),
                    "density": ComputedParam(expression="@mass", result_type="float"),
                }
            )
        )
        result = self._validate(template, version_id, "@density + 1", key="density")
        self.assertFalse(result.valid)
        self.assertIn("Cycle", result.error)

    def test_transitive_cycle_when_editing_existing_computed(self):
        # `a = @density`; editing `density` to `@a + 1` closes the loop.
        template, version_id = self._new_template_with_specs(
            ConfigSpecs(
                {
                    "mass": FloatParam(),
                    "density": ComputedParam(expression="@mass", result_type="float"),
                    "a": ComputedParam(expression="@density", result_type="float"),
                }
            )
        )
        result = self._validate(template, version_id, "@a + 1", key="density")
        self.assertFalse(result.valid)
        self.assertIn("Cycle", result.error)

    def test_syntax_error(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"a": FloatParam()})
        )
        result = self._validate(template, version_id, "@a +")
        self.assertFalse(result.valid)
        self.assertIn("Invalid expression", result.error)

    def test_empty_expression(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"a": FloatParam()})
        )
        result = self._validate(template, version_id, "   ")
        self.assertFalse(result.valid)

    def test_bad_result_type_rejected_by_dto(self):
        # result_type is a Literal on the DTO, so an invalid value is a request
        # validation error (422), not a valid=False result.
        with self.assertRaises(Exception):
            ValidateComputedParamDTO(expression="@a", result_type="bogus")

    def test_field_named_like_a_function(self):
        # `@sum` resolves to the field; the dependency graph sees it.
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"sum": FloatParam()})
        )
        result = self._validate(template, version_id, "@sum + 1")
        self.assertTrue(result.valid)
        self.assertEqual(result.referenced_keys, ["sum"])

    def test_inside_param_set_sibling_reference(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs(
                {
                    "samples": ParamSet(
                        ConfigSpecs({"mass": FloatParam(), "volume": FloatParam()})
                    ),
                }
            )
        )
        result = self._validate(
            template, version_id, "@mass / @volume", param_set_key="samples"
        )
        self.assertTrue(result.valid)
        self.assertEqual(sorted(result.referenced_keys), ["mass", "volume"])

    def test_inside_param_set_aggregate_rejected(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs(
                {
                    "samples": ParamSet(ConfigSpecs({"mass": FloatParam()})),
                }
            )
        )
        result = self._validate(
            template, version_id, "sum(@samples[].mass)", param_set_key="samples"
        )
        self.assertFalse(result.valid)
        self.assertIn("aggregate", result.error)

    def test_param_set_key_not_a_paramset(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"mass": FloatParam()})
        )
        with self.assertRaises(BadRequestException):
            self._validate(template, version_id, "@mass", param_set_key="mass")

    def test_param_set_key_unknown(self):
        template, version_id = self._new_template_with_specs(
            ConfigSpecs({"mass": FloatParam()})
        )
        with self.assertRaises(BadRequestException):
            self._validate(template, version_id, "@mass", param_set_key="nope")

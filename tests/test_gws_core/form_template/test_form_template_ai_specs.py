"""AI-assisted form-template field generation / editing (FormTemplateAiService).

The AI is prompted to return a complete field specification (a dict mapping
field key -> spec). The result is validated and RETURNED (not persisted) — the
editor applies it via the override-specs route. Single-field generation returns
one proposed field for the create/update field routes.
"""
import json
from unittest.mock import patch

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, IntParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_ai_service import FormTemplateAiService
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
    GenerateTemplateFieldDTO,
    GenerateTemplateSpecsDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase

# Patch the helper that OpenAiChat.call_gpt delegates to — no API key / network.
_GPT_TARGET = "gws_core.impl.openai.open_ai_chat.OpenAiHelper.call_gpt"


class TestFormTemplateAiSpecs(BaseTestCase):
    # ------------------------------------------------------------------ #
    # generate / modify — preview only (returns specs, no DB write)
    # ------------------------------------------------------------------ #

    def test_generate_from_scratch_returns_specs_without_persisting(self):
        template, version_id = self._empty_template()
        ai_specs = ConfigSpecs(
            {
                "full_name": StrParam(human_name="Full name"),
                "mass": FloatParam(human_name="Mass"),
            }
        ).to_json_dict()
        content_before = FormTemplateVersion.get_by_id(version_id).content
        with patch(_GPT_TARGET, return_value=json.dumps(ai_specs)):
            result = FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="a name and a mass"),
            )
        # The proposed specs are returned (dict<key, ParamSpecDTO>)...
        self.assertIn("full_name", result.specs)
        self.assertIn("mass", result.specs)
        # ...and nothing was written to the draft.
        self.assertEqual(
            FormTemplateVersion.get_by_id(version_id).content, content_before
        )

    def test_modify_returns_full_set(self):
        template, version_id = self._template_with_specs(
            ConfigSpecs({"full_name": StrParam(human_name="Full name")})
        )
        ai_specs = ConfigSpecs(
            {
                "full_name": StrParam(human_name="Full name"),
                "age": FloatParam(human_name="Age", optional=True),
            }
        ).to_json_dict()
        with patch(_GPT_TARGET, return_value=json.dumps(ai_specs)):
            result = FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="add an age field"),
            )
        self.assertIn("full_name", result.specs)
        self.assertIn("age", result.specs)

    def test_param_set_field_in_result(self):
        template, version_id = self._empty_template()
        ai_specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass"),
                            "volume": FloatParam(human_name="Volume", optional=True),
                        }
                    ),
                    human_name="Samples",
                )
            }
        ).to_json_dict()
        with patch(_GPT_TARGET, return_value=json.dumps(ai_specs)):
            result = FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="a list of samples"),
            )
        self.assertEqual(result.specs["samples"].type.value, "param_set")

    def test_current_specs_sent_to_the_ai(self):
        template, version_id = self._template_with_specs(
            ConfigSpecs({"full_name": StrParam(human_name="Full name")})
        )
        captured: dict = {}

        def _fake_call_gpt(messages):
            captured["messages"] = messages
            return json.dumps(ConfigSpecs({"full_name": StrParam()}).to_json_dict())

        with patch(_GPT_TARGET, side_effect=_fake_call_gpt):
            FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="keep it"),
            )
        payload = json.loads(captured["messages"][-1]["content"])
        self.assertIn("full_name", payload["current_specs"])
        self.assertEqual(payload["description"], "keep it")

    def test_type_catalog_is_in_system_prompt(self):
        template, version_id = self._empty_template()
        captured: dict = {}

        def _fake_call_gpt(messages):
            captured["messages"] = messages
            return json.dumps({})

        with patch(_GPT_TARGET, side_effect=_fake_call_gpt):
            FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="anything"),
            )
        system_msg = captured["messages"][0]["content"]
        self.assertIn("param_set", system_msg)
        self.assertIn("select_param", system_msg)

    def test_strips_code_fences(self):
        template, version_id = self._empty_template()
        body = json.dumps(ConfigSpecs({"name": StrParam()}).to_json_dict())
        with patch(_GPT_TARGET, return_value="```json\n" + body + "\n```"):
            result = FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="a name"),
            )
        self.assertIn("name", result.specs)

    # ------------------------------------------------------------------ #
    # invalid schema -> raise, draft left unchanged
    # ------------------------------------------------------------------ #

    def test_invalid_spec_raises_and_leaves_draft_unchanged(self):
        template, version_id = self._template_with_specs(
            ConfigSpecs({"keep": StrParam(human_name="Keep")})
        )
        content_before = FormTemplateVersion.get_by_id(version_id).content
        # An unknown param type the deserializer cannot build.
        with patch(_GPT_TARGET, return_value=json.dumps({"bad": {"type": "not_a_real_type"}})):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_specs(
                    template.id,
                    version_id,
                    GenerateTemplateSpecsDTO(description="x"),
                )
        self.assertEqual(
            FormTemplateVersion.get_by_id(version_id).content, content_before
        )

    def test_computed_cycle_raises_and_leaves_draft_unchanged(self):
        template, version_id = self._template_with_specs(
            ConfigSpecs({"keep": FloatParam(human_name="Keep")})
        )
        content_before = FormTemplateVersion.get_by_id(version_id).content
        # Two computed params referencing each other -> cycle, caught by
        # check_config_specs().
        cyclic = ConfigSpecs(
            {
                "a": ComputedParam(expression="@b + 1"),
                "b": ComputedParam(expression="@a + 1"),
            }
        ).to_json_dict()
        with patch(_GPT_TARGET, return_value=json.dumps(cyclic)):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_specs(
                    template.id,
                    version_id,
                    GenerateTemplateSpecsDTO(description="x"),
                )
        self.assertEqual(
            FormTemplateVersion.get_by_id(version_id).content, content_before
        )

    # ------------------------------------------------------------------ #
    # hard input errors -> raise
    # ------------------------------------------------------------------ #

    def test_invalid_json_raises(self):
        template, version_id = self._empty_template()
        with patch(_GPT_TARGET, return_value="this is not json"):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_specs(
                    template.id,
                    version_id,
                    GenerateTemplateSpecsDTO(description="x"),
                )

    def test_non_object_json_raises(self):
        template, version_id = self._empty_template()
        with patch(_GPT_TARGET, return_value=json.dumps([1, 2, 3])):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_specs(
                    template.id,
                    version_id,
                    GenerateTemplateSpecsDTO(description="x"),
                )

    def test_empty_description_raises(self):
        template, version_id = self._empty_template()
        with self.assertRaises(BadRequestException):
            FormTemplateAiService.generate_template_specs(
                template.id,
                version_id,
                GenerateTemplateSpecsDTO(description="   "),
            )

    def test_non_draft_version_raises(self):
        template, version_id = self._template_with_specs(
            ConfigSpecs({"name": StrParam()})
        )
        FormTemplateService.publish_version(template.id, version_id)
        with patch(_GPT_TARGET, return_value=json.dumps({})):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_specs(
                    template.id,
                    version_id,
                    GenerateTemplateSpecsDTO(description="x"),
                )

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _empty_template(self) -> tuple[FormTemplate, str]:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        return template, self._draft_id(template)

    def _template_with_specs(self, specs: ConfigSpecs) -> tuple[FormTemplate, str]:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        version_id = self._draft_id(template)
        FormTemplateVersion.get_by_id(version_id).update_specs(specs)
        return template, version_id

    def _draft_id(self, template: FormTemplate) -> str:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
            .id
        )


class TestFormTemplateAiField(BaseTestCase):
    """Single-field AI generation (generate_template_field) — no DB write."""

    def _make(self, specs: ConfigSpecs = None) -> tuple[FormTemplate, str]:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="X"))
        version_id = (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
            .id
        )
        if specs is not None:
            FormTemplateVersion.get_by_id(version_id).update_specs(specs)
        return template, version_id

    def _field_response(self, field_key: str, spec) -> str:
        return json.dumps(
            {"field_key": field_key, "spec": ConfigSpecs({field_key: spec}).to_json_dict()[field_key]}
        )

    # ------------------------------------------------------------------ #

    def test_generate_new_field_returns_key_and_spec(self):
        template, version_id = self._make()
        with patch(
            _GPT_TARGET,
            return_value=self._field_response("mass", FloatParam(human_name="Mass")),
        ):
            result = FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="a mass in grams"),
            )
        self.assertEqual(result.field_key, "mass")
        self.assertEqual(result.spec.type.value, "float")

    def test_does_not_persist(self):
        template, version_id = self._make(
            ConfigSpecs({"existing": StrParam(human_name="Existing")})
        )
        content_before = FormTemplateVersion.get_by_id(version_id).content
        with patch(
            _GPT_TARGET,
            return_value=self._field_response("mass", FloatParam(human_name="Mass")),
        ):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="a mass"),
            )
        self.assertEqual(
            FormTemplateVersion.get_by_id(version_id).content, content_before
        )

    def test_other_fields_sent_as_context_excluding_edited(self):
        template, version_id = self._make(
            ConfigSpecs(
                {
                    "name": StrParam(human_name="Name"),
                    "mass": FloatParam(human_name="Mass"),
                }
            )
        )
        captured: dict = {}

        def _fake_call_gpt(messages):
            captured["messages"] = messages
            return self._field_response("mass", FloatParam(human_name="Mass (g)"))

        with patch(_GPT_TARGET, side_effect=_fake_call_gpt):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="mass in grams", field_key="mass"),
            )
        payload = json.loads(captured["messages"][-1]["content"])
        # the field being edited is excluded from the context...
        self.assertNotIn("mass", payload["other_fields"])
        # ...but its siblings are present.
        self.assertIn("name", payload["other_fields"])
        self.assertEqual(payload["current_field_key"], "mass")

    def test_current_field_forwarded_to_ai_for_update(self):
        template, version_id = self._make(
            ConfigSpecs({"age": IntParam(human_name="Age")})
        )
        captured: dict = {}

        def _fake_call_gpt(messages):
            captured["messages"] = messages
            return self._field_response(
                "age", IntParam(human_name="Age", min_value=0, max_value=150)
            )

        with patch(_GPT_TARGET, side_effect=_fake_call_gpt):
            result = FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(
                    description="cap at 150",
                    field_key="age",
                    current_field=IntParam(human_name="Age").to_dto(),
                ),
            )
        payload = json.loads(captured["messages"][-1]["content"])
        # the current field spec is forwarded so the AI starts from it
        self.assertIsNotNone(payload["current_field"])
        self.assertEqual(payload["current_field"]["type"], "int")
        self.assertEqual(result.field_key, "age")
        self.assertEqual(result.spec.additional_info.get("max_value"), 150)

    def test_param_set_field(self):
        template, version_id = self._make()
        spec = ParamSet(
            ConfigSpecs({"mass": FloatParam(human_name="Mass")}), human_name="Samples"
        )
        with patch(_GPT_TARGET, return_value=self._field_response("samples", spec)):
            result = FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="a list of samples"),
            )
        self.assertEqual(result.field_key, "samples")
        self.assertEqual(result.spec.type.value, "param_set")

    def test_strips_code_fences(self):
        template, version_id = self._make()
        body = self._field_response("name", StrParam(human_name="Name"))
        with patch(_GPT_TARGET, return_value="```json\n" + body + "\n```"):
            result = FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="a name"),
            )
        self.assertEqual(result.field_key, "name")

    def test_invalid_key_raises(self):
        template, version_id = self._make()
        with patch(
            _GPT_TARGET,
            return_value=self._field_response_with_key("9bad", FloatParam()),
        ), self.assertRaises(BadRequestException):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="x"),
            )

    def test_missing_spec_raises(self):
        template, version_id = self._make()
        with patch(_GPT_TARGET, return_value=json.dumps({"field_key": "mass"})):
            with self.assertRaises(BadRequestException):
                FormTemplateAiService.generate_template_field(
                    template.id,
                    version_id,
                    GenerateTemplateFieldDTO(description="x"),
                )

    def test_invalid_spec_type_raises(self):
        template, version_id = self._make()
        with patch(
            _GPT_TARGET,
            return_value=json.dumps(
                {"field_key": "bad", "spec": {"type": "not_a_real_type"}}
            ),
        ), self.assertRaises(BadRequestException):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="x"),
            )

    def test_empty_description_raises(self):
        template, version_id = self._make()
        with self.assertRaises(BadRequestException):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="   "),
            )

    def test_non_draft_version_raises(self):
        template, version_id = self._make(ConfigSpecs({"name": StrParam()}))
        FormTemplateService.publish_version(template.id, version_id)
        with patch(
            _GPT_TARGET,
            return_value=self._field_response("mass", FloatParam()),
        ), self.assertRaises(BadRequestException):
            FormTemplateAiService.generate_template_field(
                template.id,
                version_id,
                GenerateTemplateFieldDTO(description="x"),
            )

    def _field_response_with_key(self, field_key: str, spec) -> str:
        # The spec is serialized under a valid key, but the returned field_key
        # is invalid — exercising the key check independently of the spec.
        return json.dumps(
            {"field_key": field_key, "spec": ConfigSpecs({"tmp": spec}).to_json_dict()["tmp"]}
        )

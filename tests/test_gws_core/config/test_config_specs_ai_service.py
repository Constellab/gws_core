"""Generic AI-assisted specs / field generation (ConfigSpecsAiService).

Pure: works on ConfigSpecs / ParamSpec only — no DB, no form template. The GPT
call is patched so no API key / network is needed.
"""
import json
from unittest.mock import patch

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.config_specs_ai_service import ConfigSpecsAiService
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, IntParam, StrParam
from gws_core.config.param.param_spec_decorator import ParamSpecCategory
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.test.base_test_case_light import BaseTestCaseLight

# OpenAiChat.call_gpt delegates to OpenAiHelper.call_gpt — patch that.
_GPT_TARGET = "gws_core.impl.openai.open_ai_chat.OpenAiHelper.call_gpt"


def _specs_json(specs: ConfigSpecs) -> str:
    return json.dumps(specs.to_json_dict())


def _field_json(key: str, spec) -> str:
    return json.dumps(
        {"field_key": key, "spec": ConfigSpecs({key: spec}).to_json_dict()[key]}
    )


class TestConfigSpecsAiService(BaseTestCaseLight):
    # ------------------------------------------------------------------ #
    # generate_specs
    # ------------------------------------------------------------------ #

    def test_generate_specs_from_scratch(self):
        ai = _specs_json(
            ConfigSpecs(
                {"name": StrParam(human_name="Name"), "mass": FloatParam(human_name="Mass")}
            )
        )
        with patch(_GPT_TARGET, return_value=ai):
            specs = ConfigSpecsAiService.generate_specs(ConfigSpecs(), "a name and a mass")
        self.assertIsInstance(specs, ConfigSpecs)
        self.assertTrue(specs.has_spec("name"))
        self.assertTrue(specs.has_spec("mass"))

    def test_generate_specs_with_computed_field(self):
        # The AI may now produce a computed_param (Formula) field; it must
        # validate (its expression references a real sibling).
        ai = _specs_json(
            ConfigSpecs(
                {
                    "quantity": IntParam(human_name="Quantity"),
                    "unit_price": FloatParam(human_name="Unit price"),
                    "total": ComputedParam(
                        expression="@quantity * @unit_price", human_name="Total"
                    ),
                }
            )
        )
        with patch(_GPT_TARGET, return_value=ai):
            specs = ConfigSpecsAiService.generate_specs(ConfigSpecs(), "a total = qty * price")
        self.assertTrue(specs.has_spec("total"))
        self.assertEqual(specs.get_spec("total").get_param_spec_type().value, "computed_param")

    def test_generate_specs_sends_current_specs(self):
        captured: dict = {}

        def _fake(messages):
            captured["messages"] = messages
            return _specs_json(ConfigSpecs({"keep": StrParam()}))

        with patch(_GPT_TARGET, side_effect=_fake):
            ConfigSpecsAiService.generate_specs(
                ConfigSpecs({"keep": StrParam(human_name="Keep")}), "tweak"
            )
        payload = json.loads(captured["messages"][-1]["content"])
        self.assertIn("keep", payload["current_specs"])
        self.assertEqual(payload["description"], "tweak")

    def test_generate_specs_invalid_raises(self):
        with patch(_GPT_TARGET, return_value=json.dumps({"bad": {"type": "nope"}})):
            with self.assertRaises(BadRequestException):
                ConfigSpecsAiService.generate_specs(ConfigSpecs(), "x")

    def test_generate_specs_empty_description_raises(self):
        with self.assertRaises(BadRequestException):
            ConfigSpecsAiService.generate_specs(ConfigSpecs(), "  ")

    def test_catalog_in_prompt_excludes_code_params(self):
        catalog = ConfigSpecsAiService._build_type_catalog()
        self.assertIn("# str", catalog)
        self.assertIn("# param_set", catalog)
        self.assertIn("min_value", catalog)
        self.assertNotIn("code_param", catalog)

    def test_catalog_includes_computed_param(self):
        catalog = ConfigSpecsAiService._build_type_catalog()
        self.assertIn("# computed_param", catalog)
        # the per-type additional_info doc for the formula expression
        self.assertIn("expression", catalog)

    def test_computed_grammar_in_both_prompts(self):
        # The expression grammar (owned by ComputedParam) is injected into both
        # prompts so the AI can author valid Formula fields.
        for template in (
            ConfigSpecsAiService.specs_system_prompt,
            ConfigSpecsAiService.field_system_prompt,
        ):
            prompt = ConfigSpecsAiService._render_prompt(template)
            self.assertIn("Formula", prompt)
            # a distinctive piece of the grammar
            self.assertIn("@@", prompt)

    # ------------------------------------------------------------------ #
    # max key length in prompt
    # ------------------------------------------------------------------ #

    def test_max_key_length_in_prompt(self):
        # The prompt advertises the same limit ConfigSpecs enforces.
        for template in (
            ConfigSpecsAiService.specs_system_prompt,
            ConfigSpecsAiService.field_system_prompt,
        ):
            prompt = ConfigSpecsAiService._render_prompt(template)
            self.assertIn(
                f"at most {ConfigSpecs.MAX_KEY_LENGTH} characters", prompt
            )

    # ------------------------------------------------------------------ #
    # category filter
    # ------------------------------------------------------------------ #

    def test_category_filter_restricts_catalog(self):
        # Only SIMPLE types -> param_set (PARAM_SET) and computed_param (COMPUTED)
        # are excluded.
        catalog = ConfigSpecsAiService._build_type_catalog(
            categories=[ParamSpecCategory.SIMPLE]
        )
        self.assertIn("# str", catalog)
        self.assertIn("# int", catalog)
        self.assertNotIn("# param_set", catalog)
        self.assertNotIn("# computed_param", catalog)

    def test_category_filter_none_keeps_all(self):
        full = ConfigSpecsAiService._build_type_catalog()
        self.assertIn("# param_set", full)
        self.assertIn("# computed_param", full)

    def test_excluding_computed_drops_grammar_from_prompt(self):
        # When COMPUTED is not offered, the formula grammar block is not injected
        # (prompt and catalog stay consistent).
        prompt = ConfigSpecsAiService._render_prompt(
            ConfigSpecsAiService.specs_system_prompt,
            categories=[ParamSpecCategory.SIMPLE],
        )
        self.assertNotIn("# computed_param", prompt)
        # the grammar's distinctive double-sigil is gone
        self.assertNotIn("@@", prompt)

    def test_category_filter_threads_through_generate_specs(self):
        captured: dict = {}

        def _fake(messages):
            captured["messages"] = messages
            return _specs_json(ConfigSpecs({"name": StrParam()}))

        with patch(_GPT_TARGET, side_effect=_fake):
            ConfigSpecsAiService.generate_specs(
                ConfigSpecs(), "a name", categories=[ParamSpecCategory.SIMPLE]
            )
        system_msg = captured["messages"][0]["content"]
        self.assertNotIn("# param_set", system_msg)
        self.assertNotIn("# computed_param", system_msg)

    # ------------------------------------------------------------------ #
    # generate_computed_expression
    # ------------------------------------------------------------------ #

    def test_generate_computed_expression_outer_scope(self):
        specs = ConfigSpecs({"mass": FloatParam(), "volume": FloatParam()})
        with patch(_GPT_TARGET, return_value="@mass / @volume"):
            expr = ConfigSpecsAiService.generate_computed_expression(
                specs, specs, "density"
            )
        self.assertEqual(expr, "@mass / @volume")

    def test_generate_computed_expression_strips_fences(self):
        specs = ConfigSpecs({"mass": FloatParam()})
        with patch(_GPT_TARGET, return_value="```\n@mass * 2\n```"):
            expr = ConfigSpecsAiService.generate_computed_expression(specs, specs, "x")
        self.assertEqual(expr, "@mass * 2")

    def test_generate_computed_expression_paramset_sends_outer_block(self):
        inner = ConfigSpecs({"mass": FloatParam()})
        outer = ConfigSpecs({"factor": FloatParam()})
        captured: dict = {}

        def _fake(messages):
            captured["messages"] = messages
            return "@mass * @@factor"

        with patch(_GPT_TARGET, side_effect=_fake):
            ConfigSpecsAiService.generate_computed_expression(
                inner, outer, "scaled mass", param_set_key="samples"
            )
        system_msg = captured["messages"][0]["content"]
        # outer scalar field is offered as an @@ reference
        self.assertIn("factor", system_msg)
        payload = json.loads(captured["messages"][-1]["content"])
        self.assertEqual(payload["param_set_key"], "samples")

    def test_generate_computed_expression_empty_response_raises(self):
        specs = ConfigSpecs({"mass": FloatParam()})
        with patch(_GPT_TARGET, return_value="   "), self.assertRaises(BadRequestException):
            ConfigSpecsAiService.generate_computed_expression(specs, specs, "x")

    def test_generate_computed_expression_empty_description_raises(self):
        specs = ConfigSpecs({"mass": FloatParam()})
        with self.assertRaises(BadRequestException):
            ConfigSpecsAiService.generate_computed_expression(specs, specs, "  ")

    def test_language_rule_in_both_prompts(self):
        # Both prompts share the language-priority rule (existing fields' language
        # first, else the description's language).
        specs_prompt = ConfigSpecsAiService._render_prompt(
            ConfigSpecsAiService.specs_system_prompt
        )
        field_prompt = ConfigSpecsAiService._render_prompt(
            ConfigSpecsAiService.field_system_prompt
        )
        for prompt in (specs_prompt, field_prompt):
            self.assertIn("SAME language as the existing fields", prompt)
            self.assertIn('language of the user\'s "description"', prompt)

    # ------------------------------------------------------------------ #
    # generate_field — create
    # ------------------------------------------------------------------ #

    def test_generate_new_field(self):
        with patch(_GPT_TARGET, return_value=_field_json("mass", FloatParam(human_name="Mass"))):
            key, spec = ConfigSpecsAiService.generate_field(ConfigSpecs(), "a mass")
        self.assertEqual(key, "mass")
        self.assertEqual(spec.get_param_spec_type().value, "float")

    def test_generate_field_sends_siblings_and_nulls_for_new(self):
        captured: dict = {}

        def _fake(messages):
            captured["messages"] = messages
            return _field_json("mass", FloatParam())

        with patch(_GPT_TARGET, side_effect=_fake):
            ConfigSpecsAiService.generate_field(
                ConfigSpecs({"name": StrParam(human_name="Name")}), "a mass"
            )
        payload = json.loads(captured["messages"][-1]["content"])
        self.assertIn("name", payload["other_fields"])
        self.assertIsNone(payload["current_field_key"])
        self.assertIsNone(payload["current_field"])

    # ------------------------------------------------------------------ #
    # generate_field — update (current_field provided)
    # ------------------------------------------------------------------ #

    def test_generate_field_update_sends_current_field(self):
        captured: dict = {}

        def _fake(messages):
            captured["messages"] = messages
            return _field_json("age", IntParam(human_name="Age", min_value=0, max_value=150))

        current = IntParam(human_name="Age")
        with patch(_GPT_TARGET, side_effect=_fake):
            key, spec = ConfigSpecsAiService.generate_field(
                ConfigSpecs({"name": StrParam()}),
                "cap age at 150",
                current_field_key="age",
                current_field=current,
            )
        payload = json.loads(captured["messages"][-1]["content"])
        self.assertEqual(payload["current_field_key"], "age")
        # the current field's spec is sent so the AI can start from it
        self.assertEqual(payload["current_field"]["type"], "int")
        self.assertEqual(key, "age")
        self.assertEqual(spec.additional_info.get("max_value"), 150)

    def test_generate_field_param_set(self):
        spec_obj = ParamSet(
            ConfigSpecs({"mass": FloatParam(human_name="Mass")}), human_name="Samples"
        )
        with patch(_GPT_TARGET, return_value=_field_json("samples", spec_obj)):
            key, spec = ConfigSpecsAiService.generate_field(ConfigSpecs(), "list of samples")
        self.assertEqual(key, "samples")
        self.assertIsInstance(spec, ParamSet)

    def test_generate_field_invalid_key_raises(self):
        with patch(_GPT_TARGET, return_value=json.dumps({"field_key": "9bad", "spec": ConfigSpecs({"t": FloatParam()}).to_json_dict()["t"]})):
            with self.assertRaises(BadRequestException):
                ConfigSpecsAiService.generate_field(ConfigSpecs(), "x")

    def test_generate_field_missing_spec_raises(self):
        with patch(_GPT_TARGET, return_value=json.dumps({"field_key": "mass"})):
            with self.assertRaises(BadRequestException):
                ConfigSpecsAiService.generate_field(ConfigSpecs(), "x")

    def test_generate_field_empty_description_raises(self):
        with self.assertRaises(BadRequestException):
            ConfigSpecsAiService.generate_field(ConfigSpecs(), "   ")

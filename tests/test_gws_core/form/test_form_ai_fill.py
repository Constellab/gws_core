"""AI-assisted form filling from text (FormAiFillService).

Voice input is handled out-of-band: the client calls ``POST /ai/transcribe-audio``
(``OpenAiTranscriptionService``) to turn audio into text, then passes that text to
``fill_values_from_text`` like any typed instruction. See test_open_ai_transcription.py.
"""
import json
from unittest.mock import patch

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form.form_ai_fill_service import FormAiFillService
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_dto import (
    CreateFormTemplateDTO,
    FormTemplateVersionStatus,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.test.base_test_case import BaseTestCase

# The instance method OpenAiChat.call_gpt delegates to OpenAiHelper.call_gpt — patch
# that so no API key / network is needed.
_GPT_TARGET = "gws_core.impl.openai.open_ai_chat.OpenAiHelper.call_gpt"


class TestFormAiFill(BaseTestCase):
    # ------------------------------------------------------------------ #
    # fill from text
    # ------------------------------------------------------------------ #

    def test_fill_from_text_returns_complete_values_without_persisting(self):
        form = self._scalar_form()
        values_before = Form.get_by_id(form.id).values
        with patch(_GPT_TARGET, return_value=json.dumps({"name": "Alice", "mass": 1.5})):
            result = FormAiFillService.fill_values_from_text(
                form.id, "set name to Alice and mass to 1.5", {}
            )
        self.assertEqual(result.values["name"], "Alice")
        self.assertEqual(result.values["mass"], 1.5)
        self.assertIn("name", result.specs)
        # The form itself must not have been modified (still the create-time
        # defaults, which fill_values_from_text returns but never persists).
        self.assertEqual(Form.get_by_id(form.id).values, values_before)

    def test_current_values_are_sent_to_the_ai(self):
        form = self._scalar_form()
        captured: dict = {}

        def _fake_call_gpt(messages):
            captured["messages"] = messages
            return json.dumps({"name": "Bob", "mass": 2.0})

        with patch(_GPT_TARGET, side_effect=_fake_call_gpt):
            FormAiFillService.fill_values_from_text(
                form.id, "change name to Bob", {"name": "Alice", "mass": 1.5}
            )
        user_msg = captured["messages"][-1]["content"]
        payload = json.loads(user_msg)
        self.assertEqual(payload["current_values"], {"name": "Alice", "mass": 1.5})
        self.assertEqual(payload["instruction"], "change name to Bob")

    def test_strips_code_fences_around_json(self):
        form = self._scalar_form()
        fenced = "```json\n" + json.dumps({"name": "Alice"}) + "\n```"
        with patch(_GPT_TARGET, return_value=fenced):
            result = FormAiFillService.fill_values_from_text(form.id, "name Alice", {})
        self.assertEqual(result.values["name"], "Alice")

    def test_compute_pipeline_runs(self):
        form = self._computed_form()
        ai_values = {"samples": [{"mass": 1.0, "volume": 0.5}]}
        with patch(_GPT_TARGET, return_value=json.dumps(ai_values)):
            result = FormAiFillService.fill_values_from_text(form.id, "one sample", {})
        self.assertEqual(
            result.values["samples"][0]["density"], {"value": 2.0, "errors": None}
        )
        self.assertEqual(result.values["total_mass"], {"value": 1.0, "errors": None})

    def test_paramset_rows_get_item_ids(self):
        form = self._paramset_form()
        ai_values = {"samples": [{"mass": 1.0, "volume": 0.5}]}
        with patch(_GPT_TARGET, return_value=json.dumps(ai_values)):
            result = FormAiFillService.fill_values_from_text(form.id, "one sample", {})
        rows = result.values["samples"]
        self.assertEqual(len(rows), 1)
        self.assertIn("__item_id", rows[0])

    def test_ai_set_computed_key_is_stripped_and_recomputed(self):
        form = self._computed_form()
        ai_values = {
            "samples": [{"mass": 1.0, "volume": 0.5}],
            "total_mass": 9999.0,  # AI wrongly set a computed key
        }
        with patch(_GPT_TARGET, return_value=json.dumps(ai_values)):
            result = FormAiFillService.fill_values_from_text(form.id, "...", {})
        # The evaluator wins.
        self.assertEqual(result.values["total_mass"], {"value": 1.0, "errors": None})

    def test_unknown_key_from_ai_is_ignored(self):
        form = self._scalar_form()
        with patch(_GPT_TARGET, return_value=json.dumps({"name": "Alice", "bogus": 1})):
            result = FormAiFillService.fill_values_from_text(form.id, "...", {})
        self.assertEqual(result.values["name"], "Alice")
        self.assertNotIn("bogus", result.values)

    # ------------------------------------------------------------------ #
    # error handling
    # ------------------------------------------------------------------ #

    def test_invalid_json_raises_bad_request(self):
        form = self._scalar_form()
        with patch(_GPT_TARGET, return_value="this is not json"):
            with self.assertRaises(BadRequestException):
                FormAiFillService.fill_values_from_text(form.id, "...", {})

    def test_non_object_json_raises_bad_request(self):
        form = self._scalar_form()
        with patch(_GPT_TARGET, return_value=json.dumps([1, 2, 3])):
            with self.assertRaises(BadRequestException):
                FormAiFillService.fill_values_from_text(form.id, "...", {})

    def test_invalid_value_type_raises_bad_request(self):
        form = self._scalar_form()
        with patch(_GPT_TARGET, return_value=json.dumps({"mass": "not a float"})):
            with self.assertRaises(BadRequestException):
                FormAiFillService.fill_values_from_text(form.id, "...", {})

    def test_empty_text_raises_bad_request(self):
        form = self._scalar_form()
        with self.assertRaises(BadRequestException):
            FormAiFillService.fill_values_from_text(form.id, "   ", {})

    # ------------------------------------------------------------------ #
    # helpers (mirror test_form_save_and_submit.py)
    # ------------------------------------------------------------------ #

    def _scalar_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "name": StrParam(human_name="Name"),
                "mass": FloatParam(human_name="Mass"),
            }
        )
        return self._make_form_from_specs(specs)

    def _paramset_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass"),
                            "volume": FloatParam(human_name="Volume", optional=True),
                        }
                    )
                )
            }
        )
        return self._make_form_from_specs(specs)

    def _computed_form(self) -> Form:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(human_name="Mass"),
                            "volume": FloatParam(human_name="Volume"),
                            "density": ComputedParam(
                                expression="mass / volume",
                                result_type="float",
                            ),
                        }
                    ),
                    optional=True,
                ),
                "total_mass": ComputedParam(
                    expression="sum(samples[].mass)", result_type="float"
                ),
            }
        )
        return self._make_form_from_specs(specs)

    def _make_form_from_specs(self, specs: ConfigSpecs) -> Form:
        template = FormTemplateService.create(CreateFormTemplateDTO(name="T"))
        draft = self._get_draft(template)
        draft.update_specs(specs)
        published = FormTemplateService.publish_version(template.id, draft.id)
        return FormService.create(CreateFormDTO(template_version_id=published.id))

    def _get_draft(self, template: FormTemplate) -> FormTemplateVersion:
        return (
            FormTemplateVersion.select()
            .where(
                (FormTemplateVersion.template == template)
                & (FormTemplateVersion.status == FormTemplateVersionStatus.DRAFT)
            )
            .get()
        )

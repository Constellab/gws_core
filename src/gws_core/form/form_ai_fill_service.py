import json
from typing import Any

from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.logger import Logger
from gws_core.form.form_dto import FormSaveResultDTO
from gws_core.form.form_service import FormService
from gws_core.impl.openai.open_ai_chat import OpenAiChat


class FormAiFillService:
    """AI-assisted form filling from a free-text instruction.

    Given a Form and the user's instruction — plus the form's current values —
    this service asks the OpenAI chat model to produce the *complete* values
    dict for the form, then runs the same validate/compute pipeline as
    ``FormService.save`` and returns a renderable ``FormSaveResultDTO``.

    It does **not** persist anything: the client renders the returned values,
    lets the user review/edit, and then calls ``POST /form/{id}/save`` as usual.

    For voice input, the client first calls ``POST /ai/transcribe-audio``
    (``OpenAiTranscriptionService``) to turn audio into text, then passes that
    text here — audio is just an alternative encoding of the instruction.

    Mirrors ``RichTextTranscriptionService`` (the existing AI + prompt-engineered
    JSON precedent in this codebase).
    """

    system_prompt = """You are an assistant that fills a structured form from a user's free-text instruction (which may itself be an audio transcription).

You are given a JSON object with two keys:
- "current_values": the form's current values, keyed by field key (param_set fields are arrays of row objects, possibly containing a "__item_id" key).
- "instruction": the user's instruction in any language.

Below this message is the form's field specification: a JSON object mapping each field KEY to its spec. Each spec contains: "type" (e.g. "str", "int", "float", "bool", "list", "param_set", ...), "human_name", "description", "optional", "default_value", and possibly "allowed_values" (an enum) and — for "param_set" fields — a nested "param_set" spec map describing each row's fields.

Rules:
- Return ONLY a single JSON object, no markdown, no code fences, no commentary, no text before or after.
- The returned object MUST contain EVERY field key from the specification (the complete values dict). Start from "current_values" and apply the instruction; keep a field's current value when the instruction does not mention it.
- Respect each field's declared "type". Use null for a field that has no value.
- If a field's spec has "allowed_values", the value MUST be exactly one of the listed values. Match the user's wording to a value handling synonyms and different languages.
- For "param_set" fields, output an array of row objects, each having the keys from that field's nested "param_set" spec. Preserve existing rows (including any "__item_id" key, verbatim) unless the instruction says to add, remove, or change rows.
- A field whose spec has "accepts_user_input": false is COMPUTED — do NOT set it (omit it or copy its current value); it will be recomputed server-side.
- Do not invent keys that are not in the specification.

Form field specification:
```
{{SPECS}}
```
"""

    @classmethod
    def fill_values_from_text(
        cls,
        form_id: str,
        text: str,
        current_values: dict[str, Any] | None,
    ) -> FormSaveResultDTO:
        """Build a renderable form payload from a text instruction. Does not persist."""
        if not text or not text.strip():
            raise BadRequestException("Provide a non-empty instruction text.")

        form = FormService.get_by_id_and_check(form_id)
        specs = form.template_version.get_content()

        ai_values = cls._ask_ai_for_values(specs, current_values or {}, text)
        return cls._build_result(specs, ai_values)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @classmethod
    def _ask_ai_for_values(
        cls,
        specs: ConfigSpecs,
        current_values: dict[str, Any],
        text: str,
    ) -> dict[str, Any]:
        prompt = cls.system_prompt.replace("{{SPECS}}", json.dumps(specs.to_json_dict()))
        chat = OpenAiChat(system_prompt=prompt)
        chat.add_user_message(json.dumps({"current_values": current_values, "instruction": text}))

        response = chat.call_gpt()
        Logger.debug(f"[FormAiFillService] AI response: {response}")

        parsed = cls._parse_json_object(response)

        # Defensive: drop any key the AI invented that is not in the specs.
        return {key: value for key, value in parsed.items() if specs.has_spec(key)}

    @classmethod
    def _parse_json_object(cls, response: str) -> dict[str, Any]:
        cleaned = cls._strip_code_fences(response)
        try:
            parsed = json.loads(cleaned)
        except Exception as err:
            raise BadRequestException(
                f"The AI returned a response that is not valid JSON: {err}"
            ) from err
        if not isinstance(parsed, dict):
            raise BadRequestException(
                "The AI response must be a JSON object mapping form field keys to values."
            )
        return parsed

    @staticmethod
    def _strip_code_fences(response: str) -> str:
        """Remove a surrounding ```...``` / ```json ... ``` fence if present."""
        text = response.strip()
        if not text.startswith("```"):
            return text
        # Drop the opening fence line (``` or ```json) and the closing fence.
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @classmethod
    def _build_result(cls, specs: ConfigSpecs, ai_values: dict[str, Any]) -> FormSaveResultDTO:
        """Run the same validate/compute pipeline as ``FormService.save`` — no DB write."""
        try:
            new_values = specs.strip_computed_keys(ai_values)
            new_values = specs.validate_values(new_values)
            computed, errors = specs.compute_values(new_values)
            new_values = specs.merge_computed(new_values, computed)
        except BadRequestException:
            raise
        except Exception as err:
            raise BadRequestException(
                f"The AI produced values that don't match the form: {err}"
            ) from err

        return FormSaveResultDTO(
            values=FormService._wrap_computed_for_response(new_values, specs, errors),
            specs=specs.to_dto(),
        )

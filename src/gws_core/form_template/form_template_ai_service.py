import json

from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.logger import Logger
from gws_core.form_template.form_template_dto import (
    GenerateComputedParamDTO,
    GenerateComputedParamResultDTO,
    ValidateComputedParamDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.impl.openai.open_ai_chat import OpenAiChat


class FormTemplateAiService:
    """AI-assisted ComputedParam expression generation.

    Given a free-text description of what a computed field should compute,
    plus the target scope (the version's outer specs, or a ParamSet's inner
    specs when ``param_set_key`` is set), this service asks the OpenAI chat
    model to produce a single ComputedParam expression. The expression is
    then validated through the same pipeline as
    :meth:`FormTemplateService.validate_computed_param`, and both the raw
    expression and its validation result are returned.

    Nothing is persisted: the editor renders the suggestion (alongside any
    validation error) and the user decides whether to keep it.

    Mirrors :class:`FormAiFillService` (text instruction → AI → validate →
    return renderable result, no DB write).
    """

    system_prompt = """You are an assistant that generates a single ComputedParam expression for a form template field, given a free-text description.

Below this message is the JSON specification of the fields available at the target scope (the keys you may reference). Each entry maps a field KEY to its spec ("type", "human_name", "description", ...). When a key whose spec type is "param_set", the spec also contains a "param_set" object describing the inner fields of each row.

ComputedParam grammar:
- Field references are written with a leading @ sigil: `@weight`, `@volume`.
- ParamSet aggregate sugar (list of values across rows): `@samples[].mass` — only valid at the OUTER scope, never inside a ParamSet row formula.
- Allowed functions: sum, mean, median, stddev, min, max, count, abs, round, sqrt, pow, concat.
- Conditional: `if(cond, a, b)`.
- Operators: + - * / % ** == != < <= > >= and or not.
- No assignments, no statements, no Python keywords other than the operators above and `if(...)`.
- A bare identifier without `@` is treated as a function name and will fail if it is not in the allowed list. Always prefix field references with `@`.

Target scope:
- When the user's request includes a `param_set_key`, your expression is the per-row formula for that ParamSet. You may reference the inner row fields by `@field`. You must NOT use aggregate sugar (`@key[].field`) in this case.
- When `param_set_key` is null, your expression is at the outer scope; both `@field` and `@key[].field` are allowed.

Output rules:
- Return ONLY the expression, as plain text on a single line.
- No `=`, no leading "result =" or similar.
- No markdown, no code fence, no commentary, no explanation, no surrounding quotes.

Available fields in the target scope:
```
{{SPECS}}
```
"""

    @classmethod
    def generate_computed_param_expression(
        cls,
        template_id: str,
        version_id: str,
        dto: GenerateComputedParamDTO,
    ) -> GenerateComputedParamResultDTO:
        """Generate a ComputedParam expression from a natural-language description.

        Does not persist anything. The returned ``expression`` is always the
        AI's verbatim output; ``validation`` is the result of running it
        through :meth:`FormTemplateService.validate_computed_param` so the
        front-end can surface the suggestion together with any error.
        """
        if not dto.description or not dto.description.strip():
            raise BadRequestException("Provide a non-empty description.")

        version = FormTemplateService.get_version(template_id, version_id)
        target_specs = FormTemplateService.resolve_computed_param_scope(
            version.get_content(), dto.param_set_key
        )

        expression = cls._ask_ai_for_expression(target_specs, dto)
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
    # Internals
    # ------------------------------------------------------------------ #

    @classmethod
    def _ask_ai_for_expression(
        cls, target_specs: ConfigSpecs, dto: GenerateComputedParamDTO
    ) -> str:
        prompt = cls.system_prompt.replace(
            "{{SPECS}}", json.dumps(target_specs.to_json_dict())
        )
        chat = OpenAiChat(system_prompt=prompt)
        chat.add_user_message(
            json.dumps(
                {"description": dto.description, "param_set_key": dto.param_set_key}
            )
        )

        response = chat.call_gpt()
        Logger.debug(f"[FormTemplateAiService] AI response: {response}")

        expression = cls._strip_code_fences(response)
        if not expression:
            raise BadRequestException("The AI returned an empty response.")
        return expression

    @staticmethod
    def _strip_code_fences(response: str) -> str:
        """Remove a surrounding ```...``` / ```json ... ``` fence if present."""
        text = response.strip()
        if not text.startswith("```"):
            return text
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

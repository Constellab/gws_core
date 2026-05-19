import json

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param_evaluator import (
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_set import ParamSet
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

Below this message is the JSON specification of the fields available at the target scope (the keys you may reference). Each entry maps a field KEY to its spec ("type", "human_name", "description", ...). When a key's spec type is "param_set", the spec also contains a "param_set" object describing the inner fields of each row.

When the target scope is a ParamSet row, a second JSON block lists the OUTER-scope fields (the ConfigSpecs that contains the ParamSet). Those keys are referenced with the double-sigil `@@name` syntax described below.

ComputedParam grammar:
- Same-scope field references use a single leading `@`: `@weight`, `@volume`.
- ParamSet aggregate sugar (list of values across rows): `@samples[].mass` — only valid at the OUTER scope, never inside a ParamSet row formula.
- Outer-scope references from inside a ParamSet row use a DOUBLE sigil: `@@factor`. Only valid when the formula lives inside a ParamSet. The target may be a plain outer field OR another outer ComputedParam — the engine resolves dependencies for you.
- The combined form `@@key[].field` (outer aggregate from inside a row) is RESERVED and rejected. Do not produce it.
- Allowed functions: {{FUNCTIONS}}.
- Conditional: `if(cond, a, b)`.
- Operators: + - * / % ** == != < <= > >= and or not.
- No assignments, no statements, no Python keywords other than the operators above and `if(...)`.
- A bare identifier without `@` is treated as a function name and will fail if it is not in the allowed list. Always prefix field references with `@` (or `@@` for outer refs).

Target scope:
- When the user's request includes a `param_set_key`, your expression is the per-row formula for that ParamSet. Reference inner row fields with `@field`; reference outer-scope fields (listed in the OUTER block) with `@@field`. You must NOT use aggregate sugar (`@key[].field`) in this case.
- When `param_set_key` is null, your expression is at the outer scope. Both `@field` and `@key[].field` are allowed. `@@field` is NOT allowed here.

Output rules:
- Return ONLY the expression, as plain text on a single line.
- No `=`, no leading "result =" or similar.
- No markdown, no code fence, no commentary, no explanation, no surrounding quotes.

Available fields in the target scope:
```
{{SPECS}}
```
{{OUTER_SPECS_BLOCK}}"""

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
        outer_specs = version.get_content()
        target_specs = FormTemplateService.resolve_computed_param_scope(
            outer_specs, dto.param_set_key
        )

        expression = cls._ask_ai_for_expression(target_specs, outer_specs, dto)
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
        cls,
        target_specs: ConfigSpecs,
        outer_specs: ConfigSpecs,
        dto: GenerateComputedParamDTO,
    ) -> str:
        # When generating a per-row formula, surface the outer-scope spec dump
        # as a separate block so the AI knows which `@@name` keys exist. At the
        # outer scope, target_specs is the outer scope itself — no extra block.
        # Filter out ParamSet siblings: `@@` cannot target an aggregate, so
        # including them would only invite invalid `@@samples` suggestions.
        if dto.param_set_key is None:
            outer_block = ""
        else:
            outer_json = outer_specs.to_json_dict()
            paramset_keys = {
                key
                for key, spec in outer_specs.get_specs_as_dict().items()
                if isinstance(spec, ParamSet)
            }
            outer_scalar_specs = {
                key: value
                for key, value in outer_json.items()
                if key not in paramset_keys
            }
            outer_block = (
                "\nAvailable outer-scope fields (reference with `@@name`):\n"
                "```\n"
                f"{json.dumps(outer_scalar_specs)}\n"
                "```\n"
            )
        functions = ", ".join(ConfigSpecsEvaluator.get_allowed_function_names())
        prompt = (
            cls.system_prompt
            .replace("{{SPECS}}", json.dumps(target_specs.to_json_dict()))
            .replace("{{OUTER_SPECS_BLOCK}}", outer_block)
            .replace("{{FUNCTIONS}}", functions)
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

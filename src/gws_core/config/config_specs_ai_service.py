import json

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecCategory
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.logger import Logger
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_json_helper import OpenAiJsonHelper


class ConfigSpecsAiService:
    """AI-assisted generation / editing of a ConfigSpecs (and of a single ParamSpec).

    Generic and context-free: it works purely on ``ConfigSpecs`` / ``ParamSpec``
    objects — no DB, no persistence, no notion of a form template, task, or
    version. Callers (e.g. ``FormTemplateAiService``) own those concerns and use
    this service to turn a free-text description into validated specs.

    Two operations, both returning validated objects (never persisting):
    - :meth:`generate_specs` — the COMPLETE field set, from a description applied
      to the current specs (empty current specs ⇒ build from scratch).
    - :meth:`generate_field` — a SINGLE field, optionally starting from the
      field's current spec (so it works for both create and update).

    The allowed field types and their JSON shapes are discovered from the
    param-spec registry via :meth:`ParamSpec.describe_for_ai` — no type is
    hard-coded here.
    """

    # Common fragment shared by the whole-specs and single-field prompts:
    # the field-key rules, the type catalog, and how to shape each spec. Keeps
    # the two prompts consistent — only the surrounding task differs.
    _field_spec_rules = """A field spec is a JSON object following the exact shape of one of the allowed field types below. Set "human_name" (a readable label) and "short_description" on every field; set "optional": true for a field the user is not required to fill. Use the type-specific keys exactly as shown — do not invent keys.

Field keys are snake_case identifiers: only letters, digits, and underscores; must not start with a digit; no spaces. Choose a key from the field's meaning (e.g. "Full name" -> "full_name").

Language of "human_name" and "short_description":
- If there are existing fields, write them in the SAME language as the existing fields' human_name / short_description.
- If there are no existing fields, write them in the language of the user's "description".

Allowed field types (each block is a real, valid example of that type's JSON shape):
```
{{TYPE_CATALOG}}
```

Field-type rules:
- Use only the field types shown above. Each block gives the type's purpose, the meaning of its "additional_info" constraint keys, and a real example — follow the example's shape exactly.
- The "additional_info" object carries per-type constraints — set them when the description implies a limit (e.g. an age between 0 and 120, a code of at most 10 characters, a multi-select). When no constraint applies, keep the additional_info keys with null values as shown in the example.
- Match each field's type to the meaning: short text -> "str", long/multi-line text -> "text", whole numbers -> "int", decimals -> "float", yes/no -> "bool", a fixed choice list -> "select_param", a calendar date -> "date_param", a repeatable group of rows -> "param_set", a value computed from other fields -> "computed_param" (a Formula)."""

    specs_system_prompt = """You design a set of fields (a field specification) from a user's free-text description, possibly modifying an existing one.

You are given a JSON object with two keys:
- "current_specs": the current fields, a JSON object mapping each field KEY to its spec (may be empty {} when building from scratch).
- "description": the user's instruction in any language.

Your job is to return the COMPLETE new field specification: a single JSON object mapping each field KEY to its spec. Start from "current_specs", apply the description, and keep untouched fields verbatim. Add, change, or remove fields only as the description asks. Keys must be unique within the object.

{{FIELD_SPEC_RULES}}

Output rules:
- Return ONLY a single JSON object mapping field keys to specs, no markdown, no code fences, no commentary, no text before or after.

The current field specification and the user description follow as a JSON object.
"""

    field_system_prompt = """You design or edit a SINGLE field from a user's free-text description.

You are given a JSON object with these keys:
- "other_fields": the sibling fields, a JSON object mapping each field KEY to its spec — read-only CONTEXT so you avoid duplicate keys and match the naming/style of siblings. Do NOT return these.
- "current_field_key": the key of the field being edited, or null when creating a new field.
- "current_field": the current spec of the field being edited, or null when creating a new field.
- "description": the user's instruction in any language.

Your job is to return ONE field: a JSON object with two keys:
- "field_key": the field's snake_case key. When "current_field_key" is given, keep it unless the description clearly asks to rename it. When it is null, choose a key from the field's meaning that does not collide with any key in "other_fields".
- "spec": the field spec (one of the allowed field types). When "current_field" is given, START FROM IT and apply the description, keeping the parts the description does not mention. When it is null, create the field from scratch.

{{FIELD_SPEC_RULES}}

Output rules:
- Return ONLY a single JSON object with exactly the keys "field_key" and "spec", no markdown, no code fences, no commentary, no text before or after.

The other fields, the current field, and the user description follow as a JSON object.
"""

    computed_expression_system_prompt = """You are an assistant that generates a single ComputedParam (Formula) expression for a field, given a free-text description.

Below this message is the JSON specification of the fields available at the target scope (the keys you may reference). Each entry maps a field KEY to its spec ("type", "human_name", "description", ...). When a key's spec type is "param_set", the spec also contains a "param_set" object describing the inner fields of each row.

When the target scope is a ParamSet row, a second JSON block lists the OUTER-scope fields (the ConfigSpecs that contains the ParamSet). Those keys are referenced with the double-sigil `@@name` syntax described below.

{{COMPUTED_GRAMMAR}}

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

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @classmethod
    def generate_specs(
        cls,
        current_specs: ConfigSpecs,
        description: str,
        categories: list[ParamSpecCategory] | None = None,
    ) -> ConfigSpecs:
        """Generate or edit the COMPLETE field set from a description.

        Returns a validated ``ConfigSpecs`` (the AI returns the full set built
        from ``current_specs`` + the description). Does not persist.

        ``categories`` optionally restricts the field types the AI may use: when
        provided, only catalog types whose ``ParamSpecCategory`` is in the list
        are offered (None ⇒ all AI-catalog types).

        Raises ``BadRequestException`` on an empty description, a JSON-parse
        failure, or a proposal that fails schema validation.
        """
        cls._check_description(description)
        parsed = cls._ask_ai_for_specs(current_specs, description, categories)
        return cls._reconstruct_and_validate(parsed)

    @classmethod
    def generate_field(
        cls,
        other_specs: ConfigSpecs,
        description: str,
        current_field_key: str | None = None,
        current_field: ParamSpec | None = None,
        categories: list[ParamSpecCategory] | None = None,
    ) -> tuple[str, ParamSpec]:
        """Generate or edit a SINGLE field from a description.

        ``other_specs`` are the sibling fields, sent as read-only context (they
        must NOT include the field being edited). ``current_field_key`` /
        ``current_field`` describe the field under edit — pass both to update an
        existing field (the AI starts from ``current_field``), or leave both
        None to create a new one. ``categories`` optionally restricts the field
        types offered (see :meth:`generate_specs`).

        Returns ``(field_key, spec)`` — both validated. Does not persist.

        Raises ``BadRequestException`` on an empty description, a JSON-parse
        failure, a malformed result, a bad key, or an unbuildable spec.
        """
        cls._check_description(description)
        chat = OpenAiChat(
            system_prompt=cls._render_prompt(cls.field_system_prompt, categories)
        )
        chat.add_user_message(
            json.dumps(
                {
                    "other_fields": other_specs.to_json_dict(),
                    "current_field_key": current_field_key,
                    "current_field": current_field.to_dto().to_json_dict()
                    if current_field is not None
                    else None,
                    "description": description,
                }
            )
        )

        response = chat.call_gpt()
        Logger.debug(f"[ConfigSpecsAiService] AI field response: {response}")
        parsed = OpenAiJsonHelper.parse_json_object(response)

        new_key = parsed.get("field_key")
        spec_json = parsed.get("spec")
        if not isinstance(new_key, str) or not new_key.strip():
            raise BadRequestException("The AI did not return a valid 'field_key'.")
        if not isinstance(spec_json, dict):
            raise BadRequestException("The AI did not return a valid 'spec' object.")

        spec = cls._reconstruct_and_validate_field(new_key, spec_json)
        return new_key, spec

    @classmethod
    def generate_computed_expression(
        cls,
        target_specs: ConfigSpecs,
        outer_specs: ConfigSpecs,
        description: str,
        param_set_key: str | None = None,
    ) -> str:
        """Generate a single ComputedParam (Formula) expression from a description.

        ``target_specs`` is the scope the formula lives in (the outer specs, or a
        ParamSet's inner specs when ``param_set_key`` is set). ``outer_specs`` is
        the enclosing scope — its scalar fields are offered as ``@@name``
        references when generating a per-row formula. Returns the raw expression
        string (fences stripped); it is NOT validated against the specs here —
        the caller runs the reference / cycle checks.

        Raises ``BadRequestException`` on an empty description or an empty AI
        response.
        """
        cls._check_description(description)

        # When generating a per-row formula, surface the outer-scope scalar
        # fields as a separate block so the AI knows which `@@name` keys exist.
        # ParamSet siblings are filtered out: `@@` cannot target an aggregate.
        if param_set_key is None:
            outer_block = ""
        else:
            outer_json = outer_specs.to_json_dict()
            paramset_keys = {
                key
                for key, spec in outer_specs.get_specs_as_dict().items()
                if isinstance(spec, ParamSet)
            }
            outer_scalar_specs = {
                key: value for key, value in outer_json.items() if key not in paramset_keys
            }
            outer_block = (
                "\nAvailable outer-scope fields (reference with `@@name`):\n"
                "```\n"
                f"{json.dumps(outer_scalar_specs)}\n"
                "```\n"
            )

        prompt = (
            cls.computed_expression_system_prompt
            .replace("{{COMPUTED_GRAMMAR}}", ComputedParam.ai_summary())
            .replace("{{SPECS}}", json.dumps(target_specs.to_json_dict()))
            .replace("{{OUTER_SPECS_BLOCK}}", outer_block)
        )
        chat = OpenAiChat(system_prompt=prompt)
        chat.add_user_message(
            json.dumps({"description": description, "param_set_key": param_set_key})
        )

        response = chat.call_gpt()
        Logger.debug(f"[ConfigSpecsAiService] AI expression response: {response}")

        expression = OpenAiJsonHelper.strip_code_fences(response)
        if not expression:
            raise BadRequestException("The AI returned an empty response.")
        return expression

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _check_description(description: str) -> None:
        if not description or not description.strip():
            raise BadRequestException("Provide a non-empty description.")

    @classmethod
    def _ask_ai_for_specs(
        cls,
        current_specs: ConfigSpecs,
        description: str,
        categories: list[ParamSpecCategory] | None = None,
    ) -> dict:
        chat = OpenAiChat(
            system_prompt=cls._render_prompt(cls.specs_system_prompt, categories)
        )
        chat.add_user_message(
            json.dumps(
                {
                    "current_specs": current_specs.to_json_dict(),
                    "description": description,
                }
            )
        )

        response = chat.call_gpt()
        Logger.debug(f"[ConfigSpecsAiService] AI specs response: {response}")
        return OpenAiJsonHelper.parse_json_object(response)

    @classmethod
    def _render_prompt(
        cls,
        template: str,
        categories: list[ParamSpecCategory] | None = None,
    ) -> str:
        """Fill the shared placeholders ({{FIELD_SPEC_RULES}}, {{TYPE_CATALOG}})
        in a prompt template.

        ``{{FIELD_SPEC_RULES}}`` is expanded first (it itself contains
        ``{{TYPE_CATALOG}}``), then the catalog is filled. The ComputedParam /
        Formula grammar rides along inside the computed_param catalog entry
        (``ComputedParam.ai_summary``), so it appears only when COMPUTED is
        offered — no separate placeholder needed.
        """
        return template.replace("{{FIELD_SPEC_RULES}}", cls._field_spec_rules).replace(
            "{{TYPE_CATALOG}}", cls._build_type_catalog(categories)
        )

    @staticmethod
    def _reconstruct_and_validate(parsed: dict) -> ConfigSpecs:
        """Rebuild a ConfigSpecs from the AI's JSON and validate it.

        Raises ``BadRequestException`` if the proposal can't be turned into
        valid ParamSpecs or fails schema validation (e.g. a computed cycle).
        """
        try:
            specs = ConfigSpecs.from_json(parsed)
            specs.check_config_specs()
        except BadRequestException:
            raise
        except Exception as err:
            raise BadRequestException(
                f"The AI produced an invalid field specification: {err}"
            ) from err
        return specs

    @staticmethod
    def _reconstruct_and_validate_field(field_key: str, spec_json: dict) -> ParamSpec:
        """Rebuild a single ParamSpec from the AI's JSON and validate it (key +
        type), reusing the same validation a single field add goes through.

        Raises ``BadRequestException`` on a bad key or an unbuildable spec.
        """
        error = ConfigSpecs._spec_key_error(field_key)
        if error is not None:
            raise BadRequestException(error)
        try:
            spec = ParamSpecHelper.create_param_spec_from_json(spec_json, validate=True)
        except BadRequestException:
            raise
        except Exception as err:
            raise BadRequestException(
                f"The AI produced an invalid field specification: {err}"
            ) from err
        return spec

    @classmethod
    def _build_type_catalog(
        cls,
        categories: list[ParamSpecCategory] | None = None,
    ) -> str:
        """Build the allowed-types catalog injected into the prompt.

        Assembled from the param-spec registry: every type that opts into the
        AI catalog (``ai_catalog_member``) describes itself via
        ``ParamSpec.describe_for_ai`` — type tag, summary, the meaning of its
        ``additional_info`` constraints, and a real example serialized exactly
        as ``ConfigSpecs.from_json`` expects. No type's shape is hard-coded
        here, so a new param type ships its own catalog entry.

        ``categories`` optionally restricts the output to types whose
        ``ParamSpecCategory`` is in the list (None ⇒ all catalog types)."""
        blocks: list[str] = []
        for param_type in ParamSpecHelper.get_param_spec_types():
            # Check the class's OWN attribute, not an inherited one — otherwise
            # subclasses (e.g. the code params extending TextParam) would leak
            # into the catalog. A type opts in only by declaring the flag itself.
            if not param_type.__dict__.get("ai_catalog_member", False):
                continue
            if categories is not None and param_type.get_category() not in categories:
                continue
            desc = param_type.describe_for_ai()
            lines = [f"# {desc.type.value} — {desc.summary}"]
            if desc.additional_info_doc:
                lines.append("additional_info keys:")
                lines.extend(
                    f"  - {key}: {meaning}" for key, meaning in desc.additional_info_doc.items()
                )
            lines.append(f"example: {json.dumps(desc.example)}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

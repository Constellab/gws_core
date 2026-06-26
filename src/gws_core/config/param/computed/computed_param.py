from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from gws_core.config.param.computed.computed_param_evaluator import (
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import (
    ParamSpecDTO,
    ParamSpecType,
    ParamSpecVisibilty,
)
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException


class ComputedParamAdditionalInfo(TypedDict):
    expression: str


@param_spec_decorator(type_=ParamSpecCategory.COMPUTED)
class ComputedParam(ParamSpec):
    """Read-only param whose value is derived from other params via an expression.

    Also referred to as a **Formula** field in the user interface.

    The user cannot submit a value for a ComputedParam. The value is recomputed
    on every save and on every read by ConfigSpecs.compute_values(...).
    """

    additional_info: ComputedParamAdditionalInfo

    # Human-facing name of this field type (it is shown as "Formula" in the UI).
    AI_FIELD_NAME = "ComputedParam (also called a Formula field)"

    # AI prompt fragment describing the expression grammar a ComputedParam /
    # Formula accepts. Folded into ai_summary so it flows through the normal
    # describe_for_ai catalog entry. Placeholder:
    #   {{FUNCTIONS}} — filled by ai_summary with the allowed function names.
    AI_EXPRESSION_GRAMMAR = """A ComputedParam (also called a Formula) field has no user-entered value: its value is computed from other fields via an EXPRESSION.

Expression grammar:
- Same-scope field references use a single leading `@`: `@weight`, `@volume`.
- ParamSet aggregate sugar (list of values across rows): `@samples[].mass` — only valid at the OUTER scope, never inside a ParamSet row formula.
- Outer-scope references from inside a ParamSet row use a DOUBLE sigil: `@@factor`. Only valid when the formula lives inside a ParamSet. The target may be a plain outer field OR another outer ComputedParam — the engine resolves dependencies for you.
- The combined form `@@key[].field` (outer aggregate from inside a row) is RESERVED and rejected. Do not produce it.
- Allowed functions: {{FUNCTIONS}}.
- Conditional: `if(cond, a, b)`.
- Operators: + - * / % ** == != < <= > >= and or not.
- No assignments, no statements, no Python keywords other than the operators above and `if(...)`.
- A bare identifier without `@` is treated as a function name and will fail if it is not in the allowed list. Always prefix field references with `@` (or `@@` for outer refs)."""

    def __init__(
        self,
        expression: str,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
    ) -> None:
        if not isinstance(expression, str) or not expression.strip():
            raise BadRequestException("ComputedParam.expression must be a non-empty string")

        self.additional_info = {
            "expression": expression,
        }
        super().__init__(
            default_value=None,
            optional=True,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @property
    def accepts_user_input(self) -> bool:
        return False

    def get_default_value(self) -> Any:
        return None

    def validate(self, value: Any) -> Any:
        # Defensive: clients must not write to a computed param. The input pass
        # in ConfigSpecs strips it before validation; we still raise here to catch
        # bugs that bypass the input pass.
        if value is not None:
            raise BadRequestException(
                "ComputedParam values are derived; submitting a value is not allowed"
            )
        return None

    @property
    def expression(self) -> str:
        return self.additional_info["expression"]

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.COMPUTED

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        # Summary + the full expression grammar (functions filled in), so the
        # generic describe_for_ai catalog entry carries everything the AI needs
        # to author a valid Formula — no bespoke method or prompt placeholder.
        functions = ", ".join(ConfigSpecsEvaluator.get_allowed_function_names())
        grammar = cls.AI_EXPRESSION_GRAMMAR.replace("{{FUNCTIONS}}", functions)
        return (
            "A ComputedParam (Formula) field — read-only, its value is computed "
            "from other fields via the 'expression' in additional_info. Use it "
            "for totals, ratios, or any value derived from other fields.\n" + grammar
        )

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        return {
            "expression": (
                "The formula computing this field's value from other fields "
                "(see the expression grammar). Reference other fields with `@key`."
            ),
        }

    @classmethod
    def ai_example_spec(cls) -> ComputedParam:
        return cls(
            expression="@quantity * @unit_price",
            human_name="Total price",
            short_description="Quantity times unit price",
        )

    @classmethod
    def empty(cls) -> ComputedParam:
        # Placeholder used by load_from_dto before fields are populated. The real
        # expression comes from spec_dto.additional_info.
        instance = cls.__new__(cls)
        instance.additional_info = {"expression": "0"}
        instance.default_value = None
        instance.optional = True
        instance.visibility = "public"
        instance.human_name = None
        instance.short_description = None
        # __init__ is bypassed via __new__, so initialize the validity state
        # that ConfigSpecs / IOSpecs read when propagating is_valid.
        instance.is_valid = True
        instance.invalid_reason = None
        return instance

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> ComputedParam:
        param_spec: ComputedParam = super().load_from_dto(spec_dto, validate=validate)
        info = spec_dto.additional_info or {}
        if "expression" not in info:
            raise BadRequestException(
                "ComputedParam DTO is missing 'expression' in additional_info"
            )
        param_spec.additional_info = {
            "expression": info["expression"],
        }
        # ComputedParam is always optional and never accepts user input
        param_spec.optional = True
        param_spec.default_value = None
        return param_spec

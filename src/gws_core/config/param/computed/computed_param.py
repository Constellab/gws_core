from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

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

    The user cannot submit a value for a ComputedParam. The value is recomputed
    on every save and on every read by ConfigSpecs.compute_values(...).
    """

    additional_info: ComputedParamAdditionalInfo

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

from typing import Any

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import (
    BoolParam,
    DictParam,
    FloatParam,
    IntParam,
    ListParam,
    ParamSpec,
    StrParam,
    TextParam,
)
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

from .param_types import ParamSpecDTO, ParamSpecType


@param_spec_decorator(category=ParamSpecCategory.DYNAMIC_PARAM)
class DynamicParam(ParamSpec):
    """Dynamic param"""

    specs: ConfigSpecs

    edition_mode: bool

    def __init__(
        self,
        specs: ConfigSpecs | None = None,
        human_name: str = "Dynamic params",
        short_description: str | None = None,
    ) -> None:
        super().__init__(
            optional=True,
            visibility="public",
            human_name=human_name,
            short_description=short_description,
            default_value=None,
        )

        self.edition_mode = True

        if specs is None:
            self.specs = ConfigSpecs()
        else:
            if isinstance(specs, dict):
                specs = ConfigSpecs(specs)

            if not isinstance(specs, ConfigSpecs):
                raise BadRequestException("The specs attribute must be an instance of ConfigSpecs.")

            self.specs = specs

        if human_name is None:
            human_name = "Dynamic params"

        self.specs.check_config_specs()

    def get_default_value(self):
        return self.specs.get_default_values()

    def build(self, value: Any) -> ConfigParamsDict:
        """Build the dynamic param value from the provided value.

        :param value: The value to build
        :type value: Any
        :return: The built value as a ConfigParamsDict
        :rtype: ConfigParamsDict
        """
        if value is None:
            return {}

        return self.specs.build_config_params(value)

    def validate(self, value: dict[str, Any]) -> dict[str, Any]:
        if value is None:
            return value

        return self.specs.get_and_check_values(value)

    def to_dto(self) -> ParamSpecDTO:
        json_ = super().to_dto()

        json_.default_value = self.get_default_value()

        json_.additional_info = {
            "specs": self.specs.to_dto(skip_private=False),
            "edition_mode": self.edition_mode,
        }

        return json_

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.DYNAMIC_PARAM

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> "DynamicParam":
        dynamic_param: DynamicParam = super().load_from_dto(spec_dto, validate=validate)

        specs = ConfigSpecs()

        if spec_dto.additional_info is None or "specs" not in spec_dto.additional_info:
            raise BadRequestException("The specs attribute is required.")

        for key, spec in spec_dto.additional_info["specs"].items():
            sub_spec_dto = ParamSpecDTO.from_json(spec)
            param_spec: ParamSpec = ParamSpecHelper.get_param_spec_type_from_str(
                sub_spec_dto.type
            ).load_from_dto(sub_spec_dto, validate=validate)
            specs.add_spec(key, param_spec)

        dynamic_param.edition_mode = spec_dto.additional_info.get("edition_mode", True)
        dynamic_param.specs = specs

        return dynamic_param

    def add_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        spec: ParamSpec = self.get_spec_from_dto(spec_dto)

        if spec.default_value is not None:
            spec.optional = True

        self.specs.add_spec(param_name, spec)

    def update_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        spec: ParamSpec = self.get_spec_from_dto(spec_dto)

        if spec.default_value is not None:
            spec.optional = True

        self.specs.update_spec(param_name, spec)

    def rename_and_update_spec(
        self, param_name: str, new_param_name: str, spec_dto: ParamSpecDTO
    ) -> None:
        spec: ParamSpec = self.get_spec_from_dto(spec_dto)

        if spec.default_value is not None:
            spec.optional = True

        self.specs.remove_spec(param_name)
        self.specs.add_spec(new_param_name, spec)

    def remove_spec(self, param_name: str) -> None:
        self.specs.remove_spec(param_name)

    def reorder_specs(self, param_names: list[str]) -> None:
        """Reorder the contained specs to match ``param_names``.

        The set of names must exactly match the current specs — no additions,
        no removals. Sending the complete order (rather than a from/to index)
        keeps the call idempotent and safe against concurrent edits.
        """
        current = list(self.specs.get_specs_as_dict().keys())
        if len(param_names) != len(set(param_names)):
            raise BadRequestException("Reorder list contains duplicate param names.")
        if set(param_names) != set(current):
            missing = sorted(set(current) - set(param_names))
            unknown = sorted(set(param_names) - set(current))
            raise BadRequestException(
                "Reorder list does not match the current dynamic params. "
                f"missing={missing}, unknown={unknown}. "
                "Refetch and retry."
            )
        self.specs.specs = {name: self.specs.get_spec(name) for name in param_names}

    def get_spec_from_dto(self, spec_dto: ParamSpecDTO) -> ParamSpec:
        return ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)

    @staticmethod
    def get_param_spec_from_type(type_: str) -> ParamSpec:
        if type_ == "str":
            return StrParam()

        if type_ == "text":
            return TextParam()

        if type_ == "bool":
            return BoolParam()

        if type_ == "int":
            return IntParam()

        if type_ == "float":
            return FloatParam()

        if type_ == "dict":
            return DictParam()

        if type_ == "list":
            return ListParam()

        raise BadRequestException(f"Invalid type for dynamic param: {type_}")

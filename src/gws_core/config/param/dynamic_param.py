from typing import Any, Dict

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import (BoolParam, DictParam, FloatParam,
                                              IntParam, ListParam, ParamSpec,
                                              StrParam, TextParam)
from gws_core.config.param.param_spec_decorator import (ParamSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from .param_types import ParamSpecDTO, ParamSpecTypeStr


@param_spec_decorator(type_=ParamSpecType.NESTED)
class DynamicParam(ParamSpec):
    """Dynamic param"""

    specs: ConfigSpecs = None

    edition_mode: bool = None

    def __init__(self, specs: ConfigSpecs = None,
                 human_name: str = 'Dynamic params',
                 short_description: str = None) -> None:
        super().__init__(optional=True,
                         visibility='public',
                         human_name=human_name,
                         short_description=short_description,
                         default_value=None)

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
            human_name = 'Dynamic params'

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

    def validate(self, value: Dict[str, Any]) -> Dict[str, Any]:
        if value is None:
            return value

        return self.specs.get_and_check_values(value)

    def to_dto(self) -> ParamSpecDTO:
        json_ = super().to_dto()

        json_.default_value = self.get_default_value()

        json_.additional_info = {
            'specs': self.specs.to_dto(skip_private=False),
            'edition_mode': self.edition_mode
        }

        return json_

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.DYNAMIC_PARAM

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO) -> "DynamicParam":
        dynamic_param: DynamicParam = super().load_from_dto(spec_dto)

        specs = ConfigSpecs()

        if spec_dto.additional_info is None or "specs" not in spec_dto.additional_info:
            raise BadRequestException("The specs attribute is required.")

        for key, spec in spec_dto.additional_info["specs"].items():
            sub_spec_dto = ParamSpecDTO.from_json(spec)
            param_spec: ParamSpec = ParamSpecHelper.get_param_spec_type_from_str(
                sub_spec_dto.type).load_from_dto(sub_spec_dto)
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

    def rename_and_update_spec(self, param_name: str, new_param_name: str, spec_dto: ParamSpecDTO) -> None:
        spec: ParamSpec = self.get_spec_from_dto(spec_dto)

        if spec.default_value is not None:
            spec.optional = True

        self.specs.remove_spec(param_name)
        self.specs.add_spec(new_param_name, spec)

    def remove_spec(self, param_name: str) -> None:
        self.specs.remove_spec(param_name)

    def get_spec_from_dto(self, spec_dto: ParamSpecDTO) -> ParamSpec:
        spec = ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)
        # TODO A VERIFIER
        if 'allowed_values' in spec.additional_info and spec.additional_info['allowed_values'] is not None and len(
                spec.additional_info['allowed_values']) == 0:
            spec.additional_info['allowed_values'] = None
        return spec

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

    @classmethod
    def get_default_value_param_spec(cls) -> "DynamicParam":
        return DynamicParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None


a: DynamicParam = DynamicParam()

# a is consider a ParamSpec

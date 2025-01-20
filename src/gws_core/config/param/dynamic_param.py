from typing import Any, Dict

from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import (BoolParam, DictParam, FloatParam,
                                              IntParam, ListParam, ParamSpec,
                                              StrParam, TextParam)
from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from .param_types import ParamSpecDTO


@param_spec_decorator(type=ParamaSpecType.NESTED)
class DynamicParam(ParamSpec[Dict[str, Any]]):
    """Dynamic param"""

    specs: ConfigSpecs = None

    edition_mode: bool = True

    def __init__(self, specs: ConfigSpecs = None,
                 human_name: str = 'Dynamic params',
                 short_description: str = None) -> None:

        if specs is None:
            self.specs = {}
        else:
            self.specs = specs

        if human_name is None:
            human_name = 'Dynamic params'

        ParamSpecHelper.check_config_specs(self.specs)

        super().__init__(optional=True,
                         visibility='public',
                         human_name=human_name,
                         short_description=short_description,
                         default_value=None)

    def get_default_value(self):
        default_value = {}
        for key, spec in self.specs.items():
            default_value[key] = spec.default_value
        return default_value

    def validate(self, value: Dict[str, Any]) -> Dict[str, Any]:
        if value is None:
            return value

        return ParamSpecHelper.get_and_check_values(self.specs, value)

    def to_dto(self) -> ParamSpecDTO:
        json_ = super().to_dto()

        json_.default_value = self.get_default_value()

        json_.additional_info = {
            'specs': {key: spec.to_dto() for key, spec in self.specs.items()},
            'edition_mode': self.edition_mode
        }

        return json_

    @classmethod
    def get_str_type(cls) -> str:
        return "dynamic"

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO) -> "DynamicParam":
        dynamic_param: DynamicParam = super().load_from_dto(spec_dto)

        dynamic_param.specs = {}

        if spec_dto.additional_info is None or "specs" not in spec_dto.additional_info:
            raise BadRequestException("The specs attribute is required.")

        for key, spec in spec_dto.additional_info["specs"].items():
            sub_spec_dto = ParamSpecDTO.from_json(spec)
            dynamic_param.specs[key] = ParamSpecHelper.get_param_spec_type_from_str(
                sub_spec_dto.type).load_from_dto(sub_spec_dto)

        dynamic_param.edition_mode = spec_dto.additional_info.get("edition_mode", True)

        return dynamic_param

    def add_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name in self.specs:
            raise BadRequestException(f"Spec with name {param_name} already exists")

        spec: ParamSpec[Any] = self.get_spec_from_dto(spec_dto)

        self.specs[param_name] = spec

    def update_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        spec: ParamSpec[Any] = self.get_spec_from_dto(spec_dto)

        self.specs[param_name] = spec

    def rename_and_update_spec(self, param_name: str, new_param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        if new_param_name in self.specs:
            raise BadRequestException(f"Spec with name {new_param_name} already exists")

        spec: ParamSpec[Any] = self.get_spec_from_dto(spec_dto)

        self.specs[new_param_name] = spec

        del self.specs[param_name]

    def remove_spec(self, param_name: str) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        del self.specs[param_name]

        if self.additional_info is not None and 'specs' in self.additional_info:
            del self.additional_info['specs'][param_name]

    def get_spec_from_dto(self, spec_dto: ParamSpecDTO) -> ParamSpec:
        spec = ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)
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

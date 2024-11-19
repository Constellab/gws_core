from typing import Any, Dict

from gws_core.config.param.param_spec import (BoolParam, DictParam, FloatParam,
                                              IntParam, ListParam, ParamSpec,
                                              StrParam, TextParam)
from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from .param_types import ParamSpecDTO, ParamSpecVisibilty


@param_spec_decorator(type=ParamaSpecType.NESTED)
class DynamicParam(ParamSpec[Dict[str, Any]]):
    """Dynamic param"""

    specs: Dict[str, ParamSpec] = None

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: str = None,
                 short_description: str = None,
                 specs: Dict[str, ParamSpec] = None) -> None:

        if specs is None:
            self.specs = {}
        else:
            self.specs = specs

        super().__init__(optional=optional,
                         visibility=visibility,
                         human_name=human_name,
                         short_description=short_description,
                         default_value={} if optional else None)

    def get_default_value(self):
        if self.optional:
            return {}
        default_value = {}
        for key, spec in self.specs.items():
            default_value[key] = spec.default_value
        return default_value

    def validate(self, value: Dict[str, Any]) -> Dict[str, Any]:
        if value is None:
            return value

        if self.specs is None:
            raise BadRequestException("The specs attribute is required.")

        if value is None:
            raise BadRequestException("The values attribute is required.")

        for key, val in self.specs.items():

            if key not in value:
                raise BadRequestException(f"The key '{key}' is required in the values dict")

            if not isinstance(val, ParamSpec):
                raise BadRequestException(f"The value of key '{key}' must be a ParamSpec")

            if not val.optional and not val.validate(value[key]):
                raise BadRequestException(f"The value of specs '{key}' is mandatory")

            if val.optional and (value[key] is None or len(str(value[key])) == 0) and val.default_value is not None:
                value[key] = val.default_value

        return value

    def to_dto(self) -> ParamSpecDTO:
        json_ = super().to_dto()

        json_.default_value = self.get_default_value()

        json_.additional_info = {
            'specs': {key: spec.to_dto() for key, spec in self.specs.items()}
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

        return dynamic_param

    def add_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name in self.specs:
            raise BadRequestException(f"Spec with name {param_name} already exists")

        spec: ParamSpec[Any] = ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)

        self.specs[param_name] = spec

    def update_spec(self, param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        spec: ParamSpec[Any] = ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)

        self.specs[param_name] = spec

    def rename_and_update_spec(self, param_name: str, new_param_name: str, spec_dto: ParamSpecDTO) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        if new_param_name in self.specs:
            raise BadRequestException(f"Spec with name {new_param_name} already exists")

        spec: ParamSpec[Any] = ParamSpecHelper.get_param_spec_type_from_str(spec_dto.type).load_from_dto(spec_dto)

        self.specs[new_param_name] = spec

        del self.specs[param_name]

    def remove_spec(self, param_name: str) -> None:
        if param_name not in self.specs:
            raise BadRequestException(f"Spec with name {param_name} not found")

        del self.specs[param_name]

        if self.additional_info is not None and 'specs' in self.additional_info:
            del self.additional_info['specs'][param_name]

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

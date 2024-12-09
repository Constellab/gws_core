

from typing import Any, Dict, List, Type, get_type_hints

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.string_helper import StringHelper

from ..config_exceptions import MissingConfigsException
from ..config_params import ConfigParams
from ..config_types import ConfigParamsDict, ConfigSpecs
from .param_spec import ParamSpec
from .param_spec_decorator import (LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST,
                                   NESTED_PARAM_SPEC_TYPES_LIST,
                                   PARAM_SPEC_TYPES_LIST,
                                   SIMPLE_PARAM_SPEC_TYPES_LIST)
from .param_types import DynamicParamAllowedSpecsDict


class ParamSpecHelper():

    @staticmethod
    def get_and_check_values(param_specs: ConfigSpecs,
                             param_values: ConfigParamsDict) -> ConfigParamsDict:
        """
        Check and validate all values based on spec
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        if param_specs is None:
            param_specs = {}
        if param_values is None:
            param_values = {}

        full_values: ConfigParamsDict = {}
        missing_params: List[str] = []

        for key, spec in param_specs.items():
            # if the config was not set
            if not key in param_values:
                if spec.optional:
                    full_values[key] = spec.get_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(spec.human_name or key)
            else:
                full_values[key] = spec.validate(param_values[key])

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return full_values

    @staticmethod
    def build_config_params(param_specs: ConfigSpecs,
                            param_values: ConfigParamsDict) -> ConfigParams:
        """
        Build the ConfigParams from the param_specs and param_values.
        ConfigParam is supposed to be used directly not stored.
        Check the param_values with params_specs and return ConfigParams if ok.
        ConfigParams contains all value and default value if not provided

        :param param_specs: [description]
        :type param_specs: ConfigSpecs
        :param param_values: [description]
        :type param_values: ConfigParamsDict
        :return: [description]
        :rtype: ConfigParams
        """
        values = ParamSpecHelper.get_and_check_values(param_specs, param_values)

        # apply transform function of specs if needed
        for key, spec in param_specs.items():
            values[key] = spec.build(values[key])

        return ConfigParams(values)

    @staticmethod
    def check_config_specs(config_specs: ConfigSpecs) -> None:
        """Check that the config specs are valid
        """
        if not config_specs:
            return

        if not isinstance(config_specs, dict):
            raise Exception("The config specs must be a dictionary")

        for key, item in config_specs.items():
            if not isinstance(item, ParamSpec):
                raise Exception(
                    f"The config spec '{key}' is invalid, it must be a ParamSpec but got {type(item)}")

    @staticmethod
    def create_param_spec_from_json(json_: Dict[str, Any]) -> ParamSpec:
        spec_dto = ParamSpecDTO.from_json(json_)

        return ParamSpecHelper.create_param_spec_from_dto(spec_dto)

    @staticmethod
    def create_param_spec_from_dto(dto: ParamSpecDTO) -> ParamSpec:
        param_spec_type = ParamSpecHelper.get_param_spec_type_from_str(dto.type)

        return param_spec_type.load_from_dto(dto)

    @staticmethod
    def get_param_spec_type_from_str(type_: str) -> Type[ParamSpec]:
        param_spec_types = ParamSpecHelper._get_param_spec_types()
        for param_spec_type in param_spec_types:
            if param_spec_type.get_str_type() == type_:
                return param_spec_type

        raise BadRequestException(f"Invalid param spec str type '{type_}'")

    @staticmethod
    def _get_param_spec_types() -> List[Type[ParamSpec]]:
        return PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_simple_param_spec_types() -> List[Type[ParamSpec]]:
        return SIMPLE_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_lab_specific_param_spec_types() -> List[Type[ParamSpec]]:
        return LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def get_nested_param_spec_types() -> List[Type[ParamSpec]]:
        return NESTED_PARAM_SPEC_TYPES_LIST

    @staticmethod
    def mandatory_values_are_set(param_specs: ConfigSpecs,
                                 param_values: ConfigParamsDict) -> bool:
        """
        check that all mandatory configs are provided
        """
        if param_specs is None:
            return True

        for key, spec in param_specs.items():
            if not spec.optional and not key in param_values:
                return False

        return True

    @staticmethod
    def get_param_spec_dto(type_: str, optional: bool, value: Any, name: str) -> ParamSpecDTO:
        human_name = StringHelper.snake_case_to_sentence(name)
        json = {
            "type": type_,
            "optional": optional,
            "visibility": "public",
            "human_name": human_name,
        }
        if value:
            json["additional_info"] = {}
            json["additional_info"]["allowed_values"] = value
        return ParamSpecDTO.from_json(json)

    @staticmethod
    def get_dynamic_param_allowed_param_spec_types(lab_allowed: bool = False) -> Dict[str, DynamicParamAllowedSpecsDict]:
        """_summary_

        :param lab_allowed: _description_, defaults to False
        :type lab_allowed: bool, optional
        :return: _description_
        :rtype: _type_
        """
        res: Dict[str, DynamicParamAllowedSpecsDict] = {}

        list_spec_types: List[type[ParamSpec]] = ParamSpecHelper.get_simple_param_spec_types().copy()
        if lab_allowed:
            list_spec_types.extend(ParamSpecHelper.get_lab_specific_param_spec_types())

        for spec_type in list_spec_types:
            annotations = get_type_hints(spec_type)
            specs: DynamicParamAllowedSpecsDict = {}

            for name, type_ in annotations.items():
                if name.isupper():
                    continue

                is_optional = type(None) in getattr(type_, '__args__', [])
                value = getattr(spec_type, name, None)

                if name == "additional_info":
                    additional_info_res: Dict[str, ParamSpecDTO] = {}
                    additional_infos_annotations = get_type_hints(type_.__args__[0])

                    for additional_info_name, additional_info_type in additional_infos_annotations.items():
                        additional_info_is_optional = type(None) in getattr(additional_info_type, '__args__', [])
                        additional_info_value = getattr(value, additional_info_name, None)
                        additional_info_type = str(
                            additional_info_type.__name__).lower() if not additional_info_is_optional else str(
                            f"{additional_info_type.__args__[0].__name__}").lower()
                        additional_info_res[additional_info_name] = ParamSpecHelper.get_param_spec_dto(
                            type_=additional_info_type, optional=additional_info_is_optional,
                            value=additional_info_value, name=additional_info_name)

                    specs[name] = additional_info_res
                else:
                    type_name: str = ''
                    if type_.__name__ == "Literal":
                        type_name = 'list'
                        value = list(type_.__args__) if type_.__args__ else None
                    elif name == "default_value":
                        type_name = spec_type.get_str_type()
                    else:
                        type_name = type_.__name__ if not is_optional else f"{type_.__args__[0].__name__}"

                    specs[name] = ParamSpecHelper.get_param_spec_dto(
                        type_=type_name, optional=is_optional, value=value, name=name
                    )

            res[spec_type.get_str_type()] = specs

        return res

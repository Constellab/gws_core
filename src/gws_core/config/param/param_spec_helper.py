# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..config_exceptions import MissingConfigsException
from ..config_params import ConfigParams
from ..config_types import ConfigParamsDict, ConfigSpecs
from .param_spec import ParamSpec
from .param_spec_decorator import PARAM_SPEC_TYPES_LIST


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

        param_spec_type = ParamSpecHelper._get_param_spec_type_from_str(spec_dto.type)

        return param_spec_type.load_from_dto(spec_dto)

    @staticmethod
    def _get_param_spec_type_from_str(type_: str) -> Type[ParamSpec]:
        param_spec_types = ParamSpecHelper._get_param_spec_types()
        for param_spec_type in param_spec_types:
            if param_spec_type.get_str_type() == type_:
                return param_spec_type

        raise BadRequestException(f"Invalid param spec str type '{type_}'")

    @staticmethod
    def _get_param_spec_types() -> List[Type[ParamSpec]]:
        return PARAM_SPEC_TYPES_LIST

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

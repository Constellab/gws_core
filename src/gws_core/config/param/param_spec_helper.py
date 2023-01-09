# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..config_exceptions import MissingConfigsException
from ..config_types import ConfigParams, ConfigSpecs
from .param_set import ParamSet
from .param_spec import (BoolParam, DictParam, FloatParam, IntParam, ListParam,
                         ParamSpec, StrParam, TextParam)
from .param_types import ParamValue
from .python_code_param import PythonCodeParam
from .tags_param_spec import TagsParam


class ParamSpecHelper():

    @staticmethod
    def get_and_check_values(param_specs: Dict[str, ParamSpec],
                             param_values: Dict[str, ParamValue]) -> Dict[str, ParamValue]:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        if param_specs is None:
            param_specs = {}
        if param_values is None:
            param_values = {}

        full_values: Dict[str, ParamValue] = {}
        missing_params: List[str] = []

        for key, spec in param_specs.items():
            # if the config was not set
            if not key in param_values:
                if spec.optional:
                    full_values[key] = spec.get_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(key)
            else:
                full_values[key] = spec.validate(param_values[key])

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return full_values

    @staticmethod
    def get_config_params(param_specs: Dict[str, ParamSpec],
                          param_values: Dict[str, ParamValue]) -> ConfigParams:
        """ Check the param_values with params_specs and return ConfigParams if ok. ConfigParams contains all value and default value if not provided

        :param param_specs: [description]
        :type param_specs: Dict[str, ParamSpec]
        :param param_values: [description]
        :type param_values: Dict[str, ParamValue]
        :return: [description]
        :rtype: ConfigParams
        """
        return ConfigParams(ParamSpecHelper.get_and_check_values(param_specs, param_values))

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
                raise Exception(f"The config spec '{key}' is invalid, it must be a ParamSpec but got {type(item)}")

    @staticmethod
    def create_param_spec_from_json(json_: Dict[str, Any]) -> ParamSpec:
        param_spec_type = ParamSpecHelper._get_param_spec_type_from_str(json_.get('type'))

        return param_spec_type.load_from_json(json_)

    @staticmethod
    def _get_param_spec_type_from_str(type_: str) -> Type[ParamSpec]:
        param_spec_types = ParamSpecHelper._get_param_spec_types()
        for param_spec_type in param_spec_types:
            if param_spec_type.get_str_type() == type_:
                return param_spec_type

        raise BadRequestException(f"Invalid param spec str type '{type_}'")

    @staticmethod
    def _get_param_spec_types() -> List[Type[ParamSpec]]:
        return [BoolParam, IntParam, FloatParam, StrParam, TextParam, ListParam, ParamSet, TagsParam,
                DictParam, PythonCodeParam]

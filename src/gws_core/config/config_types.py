

from typing import Any, Dict, Type, Union

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .param_spec import (BoolParam, DictParam, FloatParam, IntParam, ListParam,
                         ParamSpec, StrParam)

ParamValue = Union[str, int, float, bool, list, dict]
ParamValueType = Type[ParamValue]
ConfigParamsDict = Dict[str, ParamValue]


class ConfigParams(ConfigParamsDict):
    """Config values send to the task
    """

    # specification of the config
    def get_value(self, param_name: str, default_value: Any = None) -> Any:
        """
        Returns the value of a parameter by its name.

        This is different from get method.
        If the param doesn't exist or its value is None, it returns the default_value. It considers None as not defined.
        The get method only returns the default value if the param does not exists. It considers None as defined

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """

        if not self.value_is_set(param_name):
            return default_value

        return self[param_name]

    # -- P --

    def value_is_set(self, param_name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return param_name in self and self[param_name] is not None


ConfigSpecs = Dict[str, ParamSpec]


class ConfigSpecsHelper():

    @classmethod
    def check_config_specs(cls, specs: ConfigSpecs) -> None:
        """Check if the config spec is valid
        """

        if not isinstance(specs, dict):
            raise BadRequestException("The specs must be a dictionnary")

    @classmethod
    def config_specs_to_json(cls, specs: ConfigSpecs) -> Dict[str, Any]:
        """convert the config specs to json
        """
        json_: Dict[str, Any] = {}
        for key, spec in specs.items():
            json_[key] = spec.to_json()

        return json_

    @classmethod
    def config_specs_from_json(cls, dict: Dict[str, Any]) -> ConfigSpecs:
        """Create a config specs from a json
        """
        config_specs: ConfigSpecs = {}
        for key, value in dict.items():
            config_specs[key] = cls.param_spec_from_json(value)
        return config_specs

    @classmethod
    def param_spec_from_json(cls, dict: Dict[str, Any]) -> ParamSpec:
        """Create a config param from a json
        """
        config_param_type: Type[ParamSpec] = cls._get_param_spec_class_type(dict["type"])
        config_param: ParamSpec = config_param_type.empty()
        config_param.load_from_json(dict)
        return config_param

    @classmethod
    def _get_param_spec_class_type(cls, type_: str) -> Type[ParamSpec]:
        """Get the class type of ConfigParam base on type
        """
        if type_ == 'bool':
            return BoolParam
        elif type_ == 'int':
            return IntParam
        elif type_ == 'float':
            return FloatParam
        elif type_ == 'str':
            return StrParam
        elif type_ == 'list':
            return ListParam
        elif type_ == 'dict':
            return DictParam
        else:
            raise BadRequestException("Invalid type")

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, Type, Union

from .param_spec import ParamSpec

ParamValue = Union[str, int, float, bool, list, dict]
ParamValueType = Type[ParamValue]
ConfigParamsDict = Dict[str, ParamValue]
ConfigSpecs = Dict[str, ParamSpec]


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

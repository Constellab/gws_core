

from typing import Dict

from ..config.config_spec import ConfigValue
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException


# TODO voir avec ConfigValues, les 2 sont un peu similaire
class ConfigParams(Dict[str, ConfigValue]):
    """Config send to the task when running a process
    """

    # specification of the config

    def get_param(self, name: str) -> ConfigValue:
        """
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """
        if not name in self:
            raise BadRequestException(f"Parameter {name} does not exist")

        return self[name]

    # -- P --

    def param_is_set(self, name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self and self[name] is not None

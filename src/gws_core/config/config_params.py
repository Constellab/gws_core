

from typing import Dict

from ..config.config_spec import ConfigParamType
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException


class ConfigParams(Dict[str, ConfigParamType]):
    """Config send to the task when running a process
    """

    # specification of the config

    def get_param(self, name: str) -> ConfigParamType:
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

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List, final

from gws_core.config.param_spec import ParamSpec

from ..core.exception.exceptions import BadRequestException
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from .config_exceptions import MissingConfigsException
from .config_types import (ConfigSpecs, ConfigSpecsHelper, ConfigValue,
                           ConfigValues, ConfigValuesDict)


@final
@typing_registrator(unique_name="Config", object_type="MODEL", hide=True)
class Config(Viewable):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """

    _table_name = 'gws_config'

    _specs: ConfigSpecs = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self.data = {
                "specs": {},
                "values": {}
            }

    # -- A --

    def archive(self, archive: bool) -> 'Config':
        """
        Archive the config

        :param tf: True to archive, False to unarchive
        :type: `bool`
        :return: True if successfully archived, False otherwise
        :rtype: `bool`
        """
        return super().archive(archive)

    # -- C --

    # -- D --

    # -- G --

    ########################################## SPEC #####################################

    def get_specs(self) -> ConfigSpecs:
        if self._specs is None:
            self._specs = ConfigSpecsHelper.config_specs_from_json(self.data["specs"])

        return self._specs

    def set_specs(self, specs: ConfigSpecs) -> None:
        ConfigSpecsHelper.check_config_specs(specs)

        self._specs = specs
        self.data["specs"] = ConfigSpecsHelper.config_specs_to_json(specs)

    def get_spec(self, param_name: str) -> ParamSpec:
        self._check_param(param_name)

        return self.get_specs()[param_name]

    ########################################## PARAM  #####################################

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data.get("specs", {})

    def _check_param(self, param_name: str) -> None:
        if not param_name in self.get_specs():
            raise BadRequestException(f"Parameter {param_name} does not exist")

    ########################################## VALUE #####################################

    def get_values(self) -> ConfigValuesDict:
        return self.data["values"]

    def get_value(self, param_name: str) -> Any:
        """
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """

        default = self.get_spec(param_name).default_value
        return self.data.get("values", {}).get(param_name, default)

    def get_and_check_values(self) -> ConfigValues:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        values: ConfigValuesDict = self.get_values()
        specs: ConfigSpecs = self.get_specs()
        missing_params: List[str] = []

        for key, spec in specs.items():
            # if the config was not set
            if not key in values:
                if spec.optional:
                    values[key] = spec.get_and_check_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(key)

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return ConfigValues(values)

    def set_value(self, param_name: str, value: ConfigValue):
        """
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """

        value = self.get_spec(param_name).validate(value)
        if not "values" in self.data:
            self.data["values"] = {}

        self.data["values"][param_name] = value

    def set_values(self, values: ConfigValuesDict):
        """
        Set config parameters
        """
        self._clear_values()

        for k in values:
            self.set_value(k, values[k])

    def value_is_set(self, name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data["values"] and self.data["values"][name] is not None

    def _clear_values(self):
        self.data["values"] = {}

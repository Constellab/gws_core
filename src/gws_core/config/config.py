# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union, final

from ..core.classes.validator import Validator
from ..core.exception.exceptions import BadRequestException
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from .config_exceptions import MissingConfigsException
from .config_params import ConfigParams
from .config_spec import (ConfigSpecs, ConfigSpecsHelper, ConfigValue,
                          ConfigValues)


@final
@typing_registrator(unique_name="Config", object_type="MODEL", hide=True)
class Config(Viewable):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """

    _table_name = 'gws_config'

    def __init__(self, *args, specs: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self.data = {
                "specs": {},
                "params": {}
            }

        if specs:
            if not isinstance(specs, dict):
                raise BadRequestException("The specs must be a dictionnary")

            # convert type to str

            for k in specs:
                if isinstance(specs[k]["type"], type):
                    specs[k]["type"] = specs[k]["type"].__name__

                default = specs[k].get("default", None)
                if not default is None:
                    #param_t = specs[k]["type"]
                    try:
                        validator = Validator.from_specs(**specs[k])
                        default = validator.validate(default)
                        specs[k]["default"] = default
                    except Exception as err:
                        raise BadRequestException(
                            f"Invalid default config value. Error message: {err}") from err

            self.set_specs(specs)

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

    def get_param(self, name: str) -> Union[str, int, float, bool, list, dict]:
        """
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """
        if not name in self.specs:
            raise BadRequestException(f"Parameter {name} does not exist")

        default = self.specs[name].get("default", None)
        return self.data.get("params", {}).get(name, default)

    # -- P --

    def get_and_check_params(self) -> ConfigParams:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        params = self.params
        specs: ConfigSpecs = self.data["specs"]
        missing_params: List[str] = []

        for key in specs:
            # if the config was not set
            if not key in params:

                if "default" in specs[key]:
                    params[key] = specs[key]["default"]
                else:
                    # if there is not default value the value is missing
                    missing_params.append(key)

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return ConfigParams(params)

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data.get("specs", {})

    # -- R --

    # -- S --

    @property
    def params(self):
        return self.data["params"]

    def set_param(self, name: str, value: ConfigValue):
        """
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """

        value = ConfigSpecsHelper.check_config(name, value, self.specs)

        if not "params" in self.data:
            self.data["params"] = {}

        self.data["params"][name] = value

    def set_params(self, params: ConfigValues):
        """
        Set config parameters
        """
        self._clear_params()

        for k in params:
            self.set_param(k, params[k])

    @property
    def specs(self) -> dict:
        """
        Returns config specs
        """

        return self.data["specs"]

    def set_specs(self, specs: dict):
        """
        Sets the specs of the config (remove current parameters)

        :param specs: The config specs
        :type: dict
        """

        if not isinstance(specs, dict):
            raise BadRequestException("The specs must be a dictionary.")

        if self.id:
            raise BadRequestException(
                "Cannot alter the specs of a saved config")

        self.data["specs"] = specs

    def _clear_params(self):
        self.data["params"] = {}

    def param_is_set(self, name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data["params"] and self.data["params"][name] is not None

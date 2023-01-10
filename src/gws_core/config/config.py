# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, final

from ..core.model.model_with_user import ModelWithUser
from .config_exceptions import InvalidParamValueException, UnkownParamException
from .config_specs_helper import ConfigSpecsHelper
from .config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from .param.param_spec import ParamSpec
from .param.param_spec_helper import ParamSpecHelper
from .param.param_types import ParamValue


@final
class Config(ModelWithUser):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """

    _table_name = 'gws_config'

    _specs: ConfigSpecs = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved():
            self.data = {
                "specs": {},
                "values": {}
            }

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
            raise UnkownParamException(param_name)

    ########################################## VALUE #####################################

    def get_values(self) -> ConfigParamsDict:
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

    def get_and_check_values(self) -> ConfigParams:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        values: ConfigParamsDict = self.get_values()
        specs: ConfigSpecs = self.get_specs()

        return ParamSpecHelper.get_config_params(specs, values)

    def set_value(self, param_name: str, value: ParamValue):
        """
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """

        try:
            value = self.get_spec(param_name).validate(value)
        except Exception as err:
            raise InvalidParamValueException(param_name, value, str(err))

        if not "values" in self.data:
            self.data["values"] = {}

        self.data["values"][param_name] = value

    def set_values(self, values: ConfigParamsDict):
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

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        # return all the spec but the private specs
        specs: ConfigSpecs = self.get_specs()
        json_specs: dict = {}
        for key, spec in specs.items():
            if spec.visibility == 'private':
                continue
            json_specs[key] = spec.to_json()

        json_["specs"] = json_specs
        json_["values"] = self.get_values()
        return json_

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        return {}

    def export_config(self) -> dict:
        """
        Export the config to a dict
        """

        return {
            "specs": self.data["specs"],
            "values": self.get_and_check_values()
        }

    def copy(self) -> 'Config':
        """Copy the config to a new Config with a new Id
        """

        new_config: Config = Config()
        new_config.data = self.data
        return new_config

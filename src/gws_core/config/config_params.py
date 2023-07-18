# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .config_types import ConfigParamsDict

if TYPE_CHECKING:
    from .config import Config


class ConfigParams(ConfigParamsDict):
    """Config values send to the task
    """

    __config__: Config = None
    __config_model_id__: str = None

    def set_config_model_id(self, config_model_id: str) -> None:
        self.__config_model_id__ = config_model_id

    def set_config(self, config: Config) -> None:
        self.__config__ = config

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

    def value_is_set(self, param_name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return param_name in self and self[param_name] is not None

    def set_value(self, param_name: str, value: Any) -> None:
        """
        Set the value of a parameter by its name.

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter
        :type: `str`, `int`, `float`, `bool`
        """

        self[param_name] = value

        if self.__config__:
            self.__config__.set_value(param_name, value)

    def save_params(self) -> None:
        """Special method to update the config during the task run.
        The update is directly saved in the database
        /!\ To use with caution, only when you know what you are doing /!\

        :param values: values to update, other values are not changed
        :type values: ConfigParamsDict
        :return: _description_
        :rtype: OutputSpecs
        """

        if not self.__config_model_id__:
            return

        from .config import Config
        config: Config = Config.get_by_id(self.__config_model_id__)

        if config is None:
            raise Exception(
                f"Can't update the config because config with id '{self.__config_model_id__}' was not found")

        for key, value in self.items():
            config.set_value(key, value)
        config.save()

    @classmethod
    def from_config(cls, config: Config) -> ConfigParams:
        """Create a config params from a config
        """
        params = ConfigParams(config.get_values())
        params.set_config(config)
        # params.set_config_model_id(config.get_id())
        return params

    # def __getitem__(self, __k: str) -> Any:
    #     if __k not in self:
    #         raise KeyError(f"The config does not have the parameter '{__k}'")
    #     return super().__getitem__(__k)

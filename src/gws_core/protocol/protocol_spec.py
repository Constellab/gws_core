from typing import Type, TypedDict

from ..config.config_spec import ConfigValue, ConfigValues
from ..processable.processable import Processable


class ConnectorPartSpec(TypedDict):
    """Simple spec representing one side of a connector

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    processable_instance_name: str
    port_name: str


class ConnectorSpec(TypedDict):
    """Simple spec representing a connector

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    from_processable: str
    from_port: str
    to_processable: str
    to_port: str


class InterfaceSpec(TypedDict):
    """Simple spec representing an interface

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    processable_instance_name: str
    port_name: str


class ProcessableSpec():

    instance_name: str = None
    processable_type: Type[Processable] = None

    _config: ConfigValues

    def __init__(self, instance_name: str, processable_type: Type[Processable]) -> None:
        self.instance_name = instance_name
        self.processable_type = processable_type
        self._config = {}

    def configure_all(self, config_values: ConfigValues) -> 'ProcessableSpec':
        """Use to preconfigure the processable. The config must match the config specs of the processable

        :param config_name: name of the configuration (the system checks that the config exists)
        :type config_name: str
        :param config_value: value of the configuration (the system checks that it is compatible with the spec)
        :type config_value: ConfigValue
        """

        if not config_values:
            return self

        for key, value in config_values.items():
            self.configure(key, value)

        return self

    def configure(self, config_name: str, config_value: ConfigValue) -> 'ProcessableSpec':
        """Use to preconfigure the processable. The config must match the config specs of the processable

        :param config_name: name of the configuration (the system checks that the config exists)
        :type config_name: str
        :param config_value: value of the configuration (the system checks that it is compatible with the spec)
        :type config_value: ConfigValue
        """
        self._config[config_name] = config_value

        return self

    def __lshift__(self, name: str) -> ConnectorPartSpec:
        return self.get_spec(name)

    def __rshift__(self, name: str) -> ConnectorPartSpec:
        return self.get_spec(name)

    def get_spec(self, name: str) -> ConnectorPartSpec:
        return {
            "processable_instance_name": self.instance_name,
            "port_name": name,
        }

    def get_config_values(self) -> ConfigValues:
        return self._config

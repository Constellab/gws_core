

from typing import Type

from typing_extensions import TypedDict

from gws_core.config.config_params import ConfigParamsDict

from ..config.param.param_types import ParamValue
from ..process.process import Process


class ConnectorPartSpec(TypedDict):
    """Simple spec representing one side of a connector

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    process_instance_name: str
    port_name: str


class ConnectorSpec(TypedDict):
    """Simple spec representing a connector

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    from_process: str
    from_port: str
    to_process: str
    to_port: str


class InterfaceSpec(TypedDict):
    """Simple spec representing an interface

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    process_instance_name: str
    port_name: str


class ConfigMapping(TypedDict):
    """Simple spec representing a config at protocol level that is map to a process config"""
    protocol_config_name: str
    process_instance_name: str
    process_config_name: str


class ProcessSpec():

    instance_name: str = None
    process_type: Type[Process] = None

    _config: ConfigParamsDict

    def __init__(self, instance_name: str, process_type: Type[Process]) -> None:
        self.instance_name = instance_name
        self.process_type = process_type
        self._config = {}

    def set_params(self, config_params: ConfigParamsDict) -> 'ProcessSpec':
        """Use to preconfigure the process. The config must match the config specs of the process

        :param config_name: name of the configuration (the system checks that the config exists)
        :type config_name: str
        :param config_value: value of the configuration (the system checks that it is compatible with the spec)
        :type config_value: ConfigParam
        """

        if not config_params:
            return self

        for key, value in config_params.items():
            self.set_param(key, value)

        return self

    def set_param(self, param_name: str, param_value: ParamValue) -> 'ProcessSpec':
        """Use to preconfigure the process. The config must match the config specs of the process

        :param config_name: name of the configuration (the system checks that the config exists)
        :type config_name: str
        :param config_value: value of the configuration (the system checks that it is compatible with the spec)
        :type config_value: ConfigParam
        """
        self._config[param_name] = param_value

        return self

    def __lshift__(self, name: str) -> ConnectorPartSpec:
        return self.get_connector(name)

    def __rshift__(self, name: str) -> ConnectorPartSpec:
        return self.get_connector(name)

    def get_connector(self, name: str) -> ConnectorPartSpec:
        return {
            "process_instance_name": self.instance_name,
            "port_name": name,
        }

    def get_config_params(self) -> ConfigParamsDict:
        return self._config

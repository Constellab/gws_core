# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from gws_core.config.config_service import ConfigService

from ..config.config_types import ConfigParams, ConfigParamsDict, ParamValue
from ..io.port import InPort, OutPort
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .process_model import ProcessModel

if TYPE_CHECKING:
    from ..protocol.protocol_interface import IProtocol


class IProcess:

    _process_model: ProcessModel

    def __init__(self, process_model: ProcessModel) -> None:
        self._process_model = process_model

    @property
    def instance_name(self) -> str:
        return self._process_model.instance_name

    @property
    def parent_protocol(self) -> Optional[IProtocol]:
        """return the parent protocol of this process.
        If this is the main protocol (the one linked to the experiment), it returns None
        """
        from ..protocol.protocol_interface import IProtocol

        if self._process_model.parent_protocol is None:
            raise Exception(f"The process '{self.instance_name}' does not have a parent protocol")

        return IProtocol(self._process_model.parent_protocol)

    ############################################### CONFIG #########################################

    def set_param(self, param_name: str, value: ParamValue) -> None:
        """Set the param value
        """
        ConfigService.update_config_value(self._process_model.config, param_name, value)

    def set_config_params(self, config_params: ConfigParamsDict) -> None:
        """Set the config param values
        """
        ConfigService.update_config_params(self._process_model.config, config_params)

    def get_param(self, name: str) -> Any:
        return self._process_model.config.get_value(name)

    def get_config_params(self) -> ConfigParams:
        return self._process_model.config.get_and_check_values()

    def reset_config(self) -> None:
        self.set_config_params({})

    ############################################### INPUTS & OUTPUTS #########################################

    def set_input(self, name: str, resource: Resource) -> None:
        """Set the resource of an input. If you want to manually set the input resource of a process

        :param name: [description]
        :type name: str
        :param resource: [description]
        :type resource: Resource
        """
        resource_model: ResourceModel = ResourceModel.from_resource(resource)
        self._process_model.inputs.set_resource_model(port_name=name, resource_model=resource_model)

    def get_input(self, name: str) -> Resource:
        """retrieve the resource of the input

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: Resource
        """
        return self._process_model.inputs.get_resource_model(name).get_resource()

    def get_output(self, name: str) -> Resource:
        """retrieve the resource of the output

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: Resource
        """
        return self._process_model.outputs.get_resource_model(name).get_resource()

    ############################################### PORTS #########################################

    def __lshift__(self, name: str) -> InPort:
        return self._process_model.in_port(name)

    def __rshift__(self, name: str) -> OutPort:
        return self._process_model.out_port(name)

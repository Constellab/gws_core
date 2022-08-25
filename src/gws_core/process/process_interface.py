# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type

from gws_core.config.config_service import ConfigService
from gws_core.process.process import Process

from ..config.config_types import ConfigParams, ConfigParamsDict
from ..config.param_types import ParamValue
from ..io.port import InPort, OutPort
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel, ResourceOrigin
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

    def get_process_type(self) -> Type[Process]:
        return self._process_model.get_process_type()

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

        # create the resource and save it
        resource_model: ResourceModel = ResourceModel.save_from_resource(resource, origin=ResourceOrigin.UPLOADED)
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
        return self.get_output_resource_model(name).get_resource()

    def get_output_resource_model(self, name: str) -> ResourceModel:
        """retrieve the resource model of the output

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: Resource
        """
        return self._process_model.outputs.get_resource_model(name)

    ############################################### PORTS #########################################

    def __lshift__(self, name: str) -> InPort:
        return self._process_model.in_port(name)

    def __rshift__(self, name: str) -> OutPort:
        return self._process_model.out_port(name)

    def get_first_inport(self) -> InPort:
        return list(self._process_model.inputs.ports.values())[0]

    def get_first_outport(self) -> OutPort:
        return list(self._process_model.outputs.ports.values())[0]

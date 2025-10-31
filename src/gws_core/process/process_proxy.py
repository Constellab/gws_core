
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type

from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.process.process import Process
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource_dto import ResourceOrigin

from ..config.param.param_types import ParamValue
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .process_model import ProcessModel

if TYPE_CHECKING:
    from ..protocol.protocol_proxy import ProtocolProxy


class ProcessWithPort(BaseModelDTO):
    process_instance_name: str
    port_name: str


class ProcessProxy:

    _process_model: ProcessModel

    def __init__(self, process_model: ProcessModel) -> None:
        self._process_model = process_model

    @property
    def instance_name(self) -> str:
        return self._process_model.instance_name

    @property
    def parent_protocol(self) -> Optional[ProtocolProxy]:
        """return the parent protocol of this process.
        If this is the main protocol (the one linked to the scenario), it returns None
        """
        from ..protocol.protocol_proxy import ProtocolProxy

        if self._process_model.parent_protocol is None:
            raise Exception(
                f"The process '{self.instance_name}' does not have a parent protocol")

        return ProtocolProxy(self._process_model.parent_protocol)

    def get_process_type(self) -> Type[Process]:
        return self._process_model.get_process_type()

    def refresh(self) -> ProcessProxy:
        self._process_model = self._process_model.refresh()
        return self

    def get_model(self) -> ProcessModel:
        return self._process_model

    def get_model_id(self) -> str:
        return self._process_model.id

    def has_parent_protocol(self) -> bool:
        return not (self._process_model.parent_protocol is None)

    ############################################### CONFIG #########################################

    def set_param(self, param_name: str, value: ParamValue) -> None:
        """Set the param value
        """
        ProtocolService.set_process_model_config_value(
            self._process_model, param_name, value)

    def set_config_params(self, config_params: ConfigParamsDict) -> None:
        """Set the config param values
        """
        ProtocolService.configure_process_model(
            self._process_model, config_params)

    def get_param(self, name: str) -> Any:
        return self._process_model.config.get_value(name)

    def reset_config(self) -> None:
        self.set_config_params({})

    ############################################### INPUTS & OUTPUTS #########################################

    def get_input(self, name: str) -> Resource:
        """retrieve the resource of the input

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: Resource
        """
        return self.get_input_resource_model(name).get_resource()

    def get_input_resource_model(self, name: str) -> ResourceModel:
        """retrieve the resource model of the input

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: Resource
        """
        return self._process_model.inputs.get_resource_model(name)

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

    def get_input_port(self, port_name: str) -> ProcessWithPort:
        """
        Access input port information of a process to create connectors in protocol
        """
        if not self._process_model.inputs.port_exists(port_name):
            raise Exception(
                f"The process '{self.instance_name}' does not have an input port named '{port_name}'")

        return ProcessWithPort(process_instance_name=self._process_model.instance_name, port_name=port_name)

    def __lshift__(self, port_name: str) -> ProcessWithPort:
        """Visual way to access port information of a process:

        process << 'port_name'
        """

        return self.get_input_port(port_name)

    def get_output_port(self, port_name: str) -> ProcessWithPort:
        """
        Access output port information of a process to create connectors in protocol
        """
        if not self._process_model.outputs.port_exists(port_name):
            raise Exception(
                f"The process '{self.instance_name}' does not have an output port named '{port_name}'")

        return ProcessWithPort(process_instance_name=self._process_model.instance_name, port_name=port_name)

    def __rshift__(self, port_name: str) -> ProcessWithPort:
        """Visual way to access port information of a process:
        process >> 'port_name'
        """
        return self.get_output_port(port_name)

    def get_first_inport(self) -> ProcessWithPort:
        if len(self._process_model.inputs.ports) == 0:
            raise Exception(
                f"The process '{self.instance_name}' does not have any input port")

        in_port = list(self._process_model.inputs.ports.values())[0]

        return ProcessWithPort(process_instance_name=self._process_model.instance_name, port_name=in_port.name)

    def get_first_outport(self) -> ProcessWithPort:
        if len(self._process_model.outputs.ports) == 0:
            raise Exception(
                f"The process '{self.instance_name}' does not have any output port")

        out_port = list(self._process_model.outputs.ports.values())[0]

        return ProcessWithPort(process_instance_name=self._process_model.instance_name, port_name=out_port.name)

    def is_input_task(self) -> bool:
        return self._process_model.is_input_task()

    def is_output_task(self) -> bool:
        return self._process_model.is_output_task()

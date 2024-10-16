
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Tuple, Type

from gws_core.process.process import Process
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource_dto import ResourceOrigin

from ..config.config_types import ConfigParamsDict
from ..config.param.param_types import ParamValue
from ..io.port import InPort, OutPort
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .process_model import ProcessModel

if TYPE_CHECKING:
    from ..protocol.protocol_proxy import ProtocolProxy


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

    def set_input(self, name: str, resource: Resource) -> None:
        """Set the resource of an input. If you want to manually set the input resource of a process

        :param name: [description]
        :type name: str
        :param resource: [description]
        :type resource: Resource
        """

        # create the resource and save it
        resource_model: ResourceModel = ResourceModel.save_from_resource(
            resource, origin=ResourceOrigin.UPLOADED)
        self._process_model.inputs.set_resource_model(
            port_name=name, resource_model=resource_model)

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

    def __lshift__(self, name: str) -> Tuple[ProcessModel, str]:
        return (self._process_model, name)

    def __rshift__(self, name: str) -> Tuple[ProcessModel, str]:
        return (self._process_model, name)

    def get_first_inport(self) -> InPort:
        return list(self._process_model.inputs.ports.values())[0]

    def get_first_outport(self) -> OutPort:
        return list(self._process_model.outputs.ports.values())[0]

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, overload

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.io.io_spec import IOSpecDTO
from gws_core.process.process import Process
from gws_core.protocol.protocol_service import ProtocolService

from ..config.param.param_types import ParamValue
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .process_model import ProcessModel

ResourceType = TypeVar("ResourceType", bound="Resource")

if TYPE_CHECKING:
    from ..protocol.protocol_proxy import ProtocolProxy


class ProcessWithPort(BaseModelDTO):
    process_instance_name: str
    port_name: str


class ProcessProxy:
    _process_model: ProcessModel

    def __init__(self, process_model: ProcessModel) -> None:
        if not isinstance(process_model, ProcessModel):
            raise ValueError("process_model should be an instance of ProcessModel")
        self._process_model = process_model

    @property
    def instance_name(self) -> str:
        return self._process_model.instance_name

    @property
    def parent_protocol(self) -> ProtocolProxy | None:
        """return the parent protocol of this process.
        If this is the main protocol (the one linked to the scenario), it returns None
        """
        from ..protocol.protocol_proxy import ProtocolProxy

        if self._process_model.parent_protocol is None:
            raise Exception(f"The process '{self.instance_name}' does not have a parent protocol")

        return ProtocolProxy(self._process_model.parent_protocol)

    def get_process_type(self) -> type[Process]:
        return self._process_model.get_process_type()

    def refresh(self) -> ProcessProxy:
        self._process_model = self._process_model.refresh()
        return self

    def get_model(self) -> ProcessModel:
        return self._process_model

    def get_model_id(self) -> str:
        return self._process_model.id

    def has_parent_protocol(self) -> bool:
        return self._process_model.parent_protocol is not None

    ############################################### CONFIG #########################################

    def set_param(self, param_name: str, value: ParamValue) -> None:
        """Set the param value"""
        ProtocolService.set_process_model_config_value(self._process_model, param_name, value)

    def set_config_params(self, config_params: ConfigParamsDict) -> None:
        """Set the config param values"""
        ProtocolService.configure_process_model(self._process_model, config_params)

    def get_param(self, name: str) -> Any:
        return self._process_model.config.get_value(name)

    def reset_config(self) -> None:
        self.set_config_params({})

    ############################################### INPUTS & OUTPUTS #########################################

    @overload
    def get_input(self, name: str) -> Resource | None: ...

    @overload
    def get_input(self, name: str, resource_type: type[ResourceType]) -> ResourceType: ...

    def get_input(
        self, name: str, resource_type: type[ResourceType] | None = None
    ) -> Resource | ResourceType | None:
        """Retrieve the resource of the input.

        :param name: name of the input port
        :type name: str
        :param resource_type: if provided, check that the resource is of this type and return it as this type
        :type resource_type: type[Resource] | None
        :return: resource of the input
        :rtype: Resource | None
        """
        resource_model = self.get_input_resource_model(name)
        if resource_model is None:
            if resource_type is not None:
                raise Exception(
                    f"The input '{name}' of process '{self.instance_name}' is empty, expected a resource of type '{resource_type.__name__}'"
                )
            return None

        resource = resource_model.get_resource()

        if resource_type is not None and not isinstance(resource, resource_type):
            raise Exception(
                f"The input '{name}' of process '{self.instance_name}' is of type '{type(resource).__name__}', expected '{resource_type.__name__}'"
            )

        return resource

    def get_input_resource_model(self, name: str) -> ResourceModel | None:
        """retrieve the resource model of the input

        :param name: name of the input port
        :type name: str
        :return: resource model of the input
        :rtype: ResourceModel | None
        """
        self.get_input_port(name)  # check that the port exists, will raise an exception if not
        return self._process_model.inputs.get_resource_model(name)

    @overload
    def get_output(self, name: str) -> Resource | None: ...

    @overload
    def get_output(self, name: str, resource_type: type[ResourceType]) -> ResourceType: ...

    def get_output(
        self, name: str, resource_type: type[ResourceType] | None = None
    ) -> Resource | ResourceType | None:
        """Retrieve the resource of the output.

        :param name: name of the output port
        :type name: str
        :param resource_type: if provided, check that the resource is of this type and return it as this type
        :type resource_type: type[Resource] | None
        :return: resource of the output
        :rtype: Resource | None
        """
        resource_model = self.get_output_resource_model(name)
        if resource_model is None:
            if resource_type is not None:
                raise Exception(
                    f"The output '{name}' of process '{self.instance_name}' is empty, expected a resource of type '{resource_type.__name__}'"
                )
            return None

        resource = resource_model.get_resource()

        if resource_type is not None and not isinstance(resource, resource_type):
            raise Exception(
                f"The output '{name}' of process '{self.instance_name}' is of type '{type(resource).__name__}', expected '{resource_type.__name__}'"
            )

        return resource

    def get_output_resource_model(self, name: str) -> ResourceModel | None:
        """retrieve the resource model of the output

        :param name: name of the output port
        :type name: str
        :return: resource model of the output
        :rtype: ResourceModel | None
        """
        self.get_output_port(name)  # check that the port exists, will raise an exception if not
        return self._process_model.outputs.get_resource_model(name)

    def has_dynamic_inputs(self) -> bool:
        return self._process_model.inputs.is_dynamic

    def has_dynamic_outputs(self) -> bool:
        return self._process_model.outputs.is_dynamic

    ############################################### PORTS #########################################

    def get_input_port(self, port_name: str) -> ProcessWithPort:
        """
        Access input port information of a process to create connectors in protocol
        """
        if not self._process_model.inputs.port_exists(port_name):
            raise Exception(
                f"The process '{self.instance_name}' does not have an input port named '{port_name}'"
            )

        return ProcessWithPort(process_instance_name=self.instance_name, port_name=port_name)

    def get_input_ports(self) -> list[ProcessWithPort]:
        """
        Access all input port information of a process to create connectors in protocol

        :return: List of input ports
        :rtype: list[ProcessWithPort]
        """
        ports = []
        for port_name in self._process_model.inputs.ports:
            ports.append(
                ProcessWithPort(process_instance_name=self.instance_name, port_name=port_name)
            )
        return ports

    def add_dynamic_input_port(self, port_spec_dto: IOSpecDTO | None = None) -> ProcessWithPort:
        """Add a dynamic input port to the process.

        :param port_spec_dto: Optional specification for the new port
        :type port_spec_dto: IOSpecDTO | None
        :return: The newly added port
        :rtype: ProcessWithPort
        """
        if not self.has_dynamic_inputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic inputs")

        update = ProtocolService.add_dynamic_input_port_to_process(
            self._process_model.parent_protocol_id, self.instance_name, port_spec_dto
        )

        if update.process:
            self._process_model = update.process

        input_ports = self.get_input_ports()
        # return the last added port
        return input_ports[-1]

    def update_dynamic_input_port(self, port_name: str, port_spec_dto: IOSpecDTO) -> None:
        """Update the specification of a dynamic input port.

        :param port_name: Name of the port to update
        :type port_name: str
        :param port_spec_dto: New specification for the port
        :type port_spec_dto: IOSpecDTO
        """
        if not self.has_dynamic_inputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic inputs")

        update = ProtocolService.update_dynamic_input_port_of_process(
            self._process_model.parent_protocol_id, self.instance_name, port_name, port_spec_dto
        )

        if update.process:
            self._process_model = update.process

    def delete_dynamic_input_port(self, port_name: str) -> None:
        """Delete a dynamic input port from the process.

        :param port_name: Name of the port to delete
        :type port_name: str
        """
        if not self.has_dynamic_inputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic inputs")

        update = ProtocolService.delete_dynamic_input_port_of_process(
            self._process_model.parent_protocol_id, self.instance_name, port_name
        )

        if update.process:
            self._process_model = update.process

    def add_dynamic_output_port(self, port_spec_dto: IOSpecDTO | None = None) -> ProcessWithPort:
        """Add a dynamic output port to the process.

        :param port_spec_dto: Optional specification for the new port
        :type port_spec_dto: IOSpecDTO | None
        :return: The newly added port
        :rtype: ProcessWithPort
        """
        if not self.has_dynamic_outputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic outputs")

        update = ProtocolService.add_dynamic_output_port_to_process(
            self._process_model.parent_protocol_id, self.instance_name, port_spec_dto
        )

        if update.process:
            self._process_model = update.process

        output_ports = self.get_output_ports()
        # return the last added port
        return output_ports[-1]

    def update_dynamic_output_port(self, port_name: str, port_spec_dto: IOSpecDTO) -> None:
        """Update the specification of a dynamic output port.

        :param port_name: Name of the port to update
        :type port_name: str
        :param port_spec_dto: New specification for the port
        :type port_spec_dto: IOSpecDTO
        """
        if not self.has_dynamic_outputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic outputs")

        update = ProtocolService.update_dynamic_output_port_of_process(
            self._process_model.parent_protocol_id, self.instance_name, port_name, port_spec_dto
        )

        if update.process:
            self._process_model = update.process

    def delete_dynamic_output_port(self, port_name: str) -> None:
        """Delete a dynamic output port from the process.

        :param port_name: Name of the port to delete
        :type port_name: str
        """
        if not self.has_dynamic_outputs():
            raise Exception(f"The process '{self.instance_name}' does not have dynamic outputs")

        update = ProtocolService.delete_dynamic_output_port_of_process(
            self._process_model.parent_protocol_id, self.instance_name, port_name
        )

        if update.process:
            self._process_model = update.process

    ############################################### DYNAMIC CONFIG #########################################

    def add_dynamic_param(
        self, config_spec_name: str, param_name: str, spec_dto: ParamSpecDTO
    ) -> None:
        """Add a dynamic parameter specification to the process.

        :param config_spec_name: Name of the dynamic config spec (e.g. 'params')
        :type config_spec_name: str
        :param param_name: Name of the parameter to add
        :type param_name: str
        :param spec_dto: Specification of the parameter
        :type spec_dto: ParamSpecDTO
        """
        update = ProtocolService.add_dynamic_param_spec_of_process(
            self._process_model.parent_protocol_id,
            self.instance_name,
            config_spec_name,
            param_name,
            spec_dto,
        )

        if update.process:
            self._process_model = update.process

    def update_dynamic_param(
        self, config_spec_name: str, param_name: str, spec_dto: ParamSpecDTO
    ) -> None:
        """Update a dynamic parameter specification of the process.

        :param config_spec_name: Name of the dynamic config spec (e.g. 'params')
        :type config_spec_name: str
        :param param_name: Name of the parameter to update
        :type param_name: str
        :param spec_dto: New specification of the parameter
        :type spec_dto: ParamSpecDTO
        """
        update = ProtocolService.update_dynamic_param_spec_of_process(
            self._process_model.parent_protocol_id,
            self.instance_name,
            config_spec_name,
            param_name,
            spec_dto,
        )

        if update.process:
            self._process_model = update.process

    def remove_dynamic_param(self, config_spec_name: str, param_name: str) -> None:
        """Remove a dynamic parameter specification from the process.

        :param config_spec_name: Name of the dynamic config spec (e.g. 'params')
        :type config_spec_name: str
        :param param_name: Name of the parameter to remove
        :type param_name: str
        """
        update = ProtocolService.remove_dynamic_param_spec_of_process(
            self._process_model.parent_protocol_id,
            self.instance_name,
            config_spec_name,
            param_name,
        )

        if update.process:
            self._process_model = update.process

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
                f"The process '{self.instance_name}' does not have an output port named '{port_name}'"
            )

        return ProcessWithPort(process_instance_name=self.instance_name, port_name=port_name)

    def get_output_ports(self) -> list[ProcessWithPort]:
        """
        Access all output port information of a process to create connectors in protocol

        :return: List of output ports
        :rtype: list[ProcessWithPort]
        """
        ports = []
        for port_name in self._process_model.outputs.ports:
            ports.append(
                ProcessWithPort(process_instance_name=self.instance_name, port_name=port_name)
            )
        return ports

    def __rshift__(self, port_name: str) -> ProcessWithPort:
        """Visual way to access port information of a process:
        process >> 'port_name'
        """
        return self.get_output_port(port_name)

    def get_first_inport(self) -> ProcessWithPort:
        if len(self._process_model.inputs.ports) == 0:
            raise Exception(f"The process '{self.instance_name}' does not have any input port")

        in_port = list(self._process_model.inputs.ports.values())[0]

        return ProcessWithPort(process_instance_name=self.instance_name, port_name=in_port.name)

    def get_first_outport(self) -> ProcessWithPort:
        if len(self._process_model.outputs.ports) == 0:
            raise Exception(f"The process '{self.instance_name}' does not have any output port")

        out_port = list(self._process_model.outputs.ports.values())[0]

        return ProcessWithPort(
            process_instance_name=self._process_model.instance_name, port_name=out_port.name
        )

    def is_input_task(self) -> bool:
        return self._process_model.is_input_task()

    def is_output_task(self) -> bool:
        return self._process_model.is_output_task()

    ############################################### RESET & DELETE #########################################

    def reset_process(self) -> None:
        """Reset the process, clearing its execution results and impacted entities."""
        EntityNavigatorService.reset_process_of_protocol_id(
            self._process_model.parent_protocol_id, self.instance_name
        )

    def delete_process(self) -> None:
        """Delete the process from its parent protocol.
        If the process is not in draft status, it is reset first.
        """
        if not self._process_model.is_draft:
            self.reset_process()

        ProtocolService.delete_process_of_protocol_id(
            self._process_model.parent_protocol_id, self.instance_name
        )

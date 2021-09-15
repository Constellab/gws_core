# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..config.config_types import ParamValue
from ..io.port import InPort, OutPort
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .process_model import ProcessModel

if TYPE_CHECKING:
    from ..protocol.protocol_interface import IProtocol


class IProcess:

    _process_model: ProcessModel
    _parent_protocol: Optional[IProtocol]

    def __init__(self, process_model: ProcessModel, parent_protocol: Optional[IProtocol]) -> None:
        self._process_model = process_model
        self._parent_protocol = parent_protocol

    def set_param(self, name: str, value: ParamValue) -> None:
        """Set the param value

        :param name: [description]
        :type name: str
        :param value: [description]
        :type value: ParamValue
        """
        self._process_model.set_param(name, value)

    def get_param(self, name: str) -> Any:
        return self._process_model.set_config_param(name)

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

    @property
    def instance_name(self) -> str:
        return self._process_model.instance_name

    @property
    def parent_protocol(self) -> Optional[IProtocol]:
        """return the parent protocol of this process.
        If this is the main protocol (the one linked to the experiment), it returns None
        """
        return self._parent_protocol

    def __lshift__(self, name: str) -> InPort:
        return self._process_model.in_port(name)

    def __rshift__(self, name: str) -> OutPort:
        return self._process_model.out_port(name)

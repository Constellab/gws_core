# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from gws_core.protocol.protocol_dto import ConnectorDTO

from ..process.process_model import ProcessModel
from .io_exception import ImcompatiblePortsException
from .port import InPort, OutPort


@final
class Connector:
    """
    Connector class representing the connection of two Ports.

    :param in_port: Left-hand side in_port
    :type in_port: InPort
    :param out_port: Right-hand side out_port
    :type out_port: OutPort
    """
    left_process: ProcessModel = None
    right_process: ProcessModel = None

    left_port_name: str = None
    right_port_name: str = None

    def __init__(self, left_process: ProcessModel,
                 right_process: ProcessModel,
                 left_port_name: str,
                 right_port_name: str,
                 check_compatiblity: bool = True) -> None:
        self.left_process = left_process
        self.right_process = right_process

        self.left_port_name = left_port_name
        self.right_port_name = right_port_name

        left_port: OutPort = self.left_port
        right_port: InPort = self.right_port

        if check_compatiblity and not left_port.resource_spec.is_compatible_with_in_spec(right_port.resource_spec):
            raise ImcompatiblePortsException(
                out_port=left_port, in_port=right_port)

        # Automatically propagate the resource if the left port has a resource
        if left_port.resource_provided:
            self.propagate_resource()

    def to_dto(self) -> ConnectorDTO:
        return ConnectorDTO.from_json({
            "from": {
                "node": self.left_process.instance_name,
                "port": self.left_port_name,
            },
            "to": {
                "node": self.right_process.instance_name,
                "port": self.right_port_name,
            }
        })

    def propagate_resource(self) -> bool:
        """
        Propagate the resource from the output port to the input port.

        :return: True if the resource was propagated, False otherwise
        :rtype: bool
        """

        if not self.left_port.resource_provided:
            return False

        # if the resource was already propagated, we don't propagate it again
        if self.right_port.resource_provided and self.right_port.resource_model.id == self.left_port.resource_model.id:
            return False

        # Get the resource from the output port
        resource = self.left_port.resource_model

        # Set the resource to the input port
        self.right_port.resource_model = resource

        return True

    @property
    def left_port(self) -> OutPort:
        """
        Returns the left-hand side process

        :return: The left-hand side process
        :rtype: process
        """
        return self.left_process.out_port(self.left_port_name)

    @property
    def right_port(self) -> InPort:
        """
        Returns the right-hand side process

        :return: The right-hand side process
        :rtype: process
        """
        return self.right_process.in_port(self.right_port_name)

    def is_connected_to(self, process_model: ProcessModel) -> bool:
        """return true if the connector is connected to the process model
        """
        return process_model in (self.left_process, self.right_process)

    def is_right_connected_to(self, process_model_name: str, port_name: str) -> bool:
        """ return true if the right side is the specified process connected to the specified port
        """
        return self.right_process.instance_name == process_model_name and self.right_port_name == port_name

    def is_left_connected_to(self, process_model_name: str, port_name: str) -> bool:
        """ return true if the left side is the specified process connected to the specified port
        """
        return self.left_process.instance_name == process_model_name and self.left_port_name == port_name

    def reset_right_port(self) -> None:
        """ reset the right port
        """
        self.right_port.reset()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connector):
            return False
        return self.left_port == other.left_port and self.right_port == other.right_port

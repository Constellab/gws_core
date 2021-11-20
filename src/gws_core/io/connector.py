from typing import final

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
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

    in_port: InPort = None
    out_port: OutPort = None

    def __init__(self, out_port: OutPort, in_port: InPort, check_compatiblity: bool = True):
        if not isinstance(in_port, InPort):
            raise BadRequestException(
                "The input port must be an instance of InPort")

        if not isinstance(out_port, OutPort):
            raise BadRequestException(
                "The output port must be an instance of OutPort")

        if in_port.is_left_connected:
            raise BadRequestException("The right-hand side port is already connected")

        source_process = out_port.parent.parent
        target_process = in_port.parent.parent

        if in_port.parent is None or target_process is None:
            raise BadRequestException(
                "The input port is not associated with a process")

        if out_port.parent is None or source_process is None:
            raise BadRequestException(
                "The output port is not associated with a process")

        # hard checking of port compatibility
        # if check_compatiblity and not out_port.resource_spec.is_compatible_with_spec(in_port.resource_spec):
        #    raise ImcompatiblePortsException(out_port=out_port, in_port=in_port)

        self.in_port = in_port
        self.out_port = out_port

        # Add inport to the next of outport
        out_port.add_next(in_port)
        # Set outport as previous of inport
        in_port.set_previous(out_port)

    def disconnect(self) -> None:
        self.in_port.disconnect()
        self.out_port.disconnect()

    # -- V --
    def to_json(self, deep: bool = False) -> dict:
        """
        Returns a dictionnary describing the Connector.

        :return: A dictionnary describing the Connector
        :rtype: dict
        """

        r_id = ""

        if self.out_port.resource_model:
            r_id = self.out_port.resource_model.id

        link = {
            "from": {
                "node": self.left_process.instance_name,
                "port": self.out_port.name,
            },
            "to": {
                "node": self.right_process.instance_name,
                "port": self.in_port.name,
            },
            "resource_id": r_id
        }

        return link

    # -- L --

    @property
    def left_process(self) -> ProcessModel:
        """
        Returns the left-hand side process

        :return: The left-hand side process
        :rtype: process
        """
        return self.out_port.parent.parent

    # -- L --

    # -- O --

    @property
    def right_process(self) -> ProcessModel:
        """
        Returns the right-hand side process

        :return: The right-hand side process
        :rtype: process
        """
        return self.in_port.parent.parent

    def is_connected_to(self, process_model: ProcessModel) -> bool:
        """return true if the connector is connected to the process model
        """
        return process_model in (self.left_process, self.right_process)

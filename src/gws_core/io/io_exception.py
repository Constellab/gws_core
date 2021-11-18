
from __future__ import annotations

from typing import TYPE_CHECKING, List, Type

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from .io_spec import IOSpecClass

if TYPE_CHECKING:
    from ..io.port import InPort, OutPort
    from ..resource.resource import Resource


class ResourceNotCompatibleException(BadRequestException):
    """Error raise when we try to set the port resource with an incompatible resource

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    port_name: str
    resource_type: Type[Resource]
    spec: IOSpecClass

    def __init__(self, port_name: str, resource_type: Type[Resource],  spec: IOSpecClass) -> None:
        self.port_name = port_name
        self.resource_type = resource_type
        self.excepted_types = spec
        super().__init__(
            detail=GWSException.RESOURCE_NOT_COMPATIBLE.value,
            unique_code=GWSException.RESOURCE_NOT_COMPATIBLE.name,
            detail_args={"port": port_name, "resource_type": resource_type, "expected_types": spec.to_resource_types()})


class MissingInputResourcesException(BadRequestException):
    """Raised when 1 or more input resources was not provided

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    port_names: List[str]

    def __init__(self, port_names: List[str]) -> None:
        self.port_names = port_names
        super().__init__(
            detail=GWSException.MISSING_INPUT_RESOURCES.value,
            unique_code=GWSException.MISSING_INPUT_RESOURCES.name,
            detail_args={"port_names": ",".join(port_names)})


class ImcompatiblePortsException(BadRequestException):
    """ Exception raised when trying to create a Connector but the port a imcompatible

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    out_port: OutPort = None
    in_port: InPort = None

    def __init__(self, out_port: OutPort, in_port: InPort) -> None:
        self.in_port = in_port
        self.out_port = out_port
        super().__init__(
            detail=GWSException.IMCOMPATIBLE_PORT.value,
            unique_code=GWSException.IMCOMPATIBLE_PORT.name,
            detail_args={"out_port_name": out_port.name, "out_port_types": out_port.resource_spec.to_resource_types(),
                         "in_port_name": in_port.name, "in_port_types": in_port.resource_spec.to_resource_types()})


class InvalidOutputException(Exception):
    pass


# class ConnectorCreationException(BadRequestException):
#     """ Exception raised when an exception on

#     :param BadRequestException: [description]
#     :type BadRequestException: [type]
#     """

#     out_port: OutPort = None
#     in_port: InPort = None

#     def __init__(self, out_port: OutPort, in_port: InPort) -> None:
#         self.in_port = in_port
#         self.out_port = out_port
#         super().__init__(
#             detail=GWSException.IMCOMPATIBLE_PORT.value,
#             unique_code=GWSException.IMCOMPATIBLE_PORT.name,
#             detail_args={"out_port_name": out_port.name, "out_port_types": out_port.resource_spec.to_resource_types(),
#                          "in_port_name": in_port.name, "in_port_types": in_port.resource_spec.to_resource_types()})

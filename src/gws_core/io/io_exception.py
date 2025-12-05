from __future__ import annotations

from typing import TYPE_CHECKING

from gws_core.io.io_spec import IOSpec

from ..core.exception.exceptions.bad_request_exception import BadRequestException
from ..core.exception.gws_exceptions import GWSException

if TYPE_CHECKING:
    from ..io.port import InPort, OutPort
    from ..resource.resource import Resource


class ResourceNotCompatibleException(BadRequestException):
    """Error raise when we try to set the port resource with an incompatible resource

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    port_name: str
    resource_type: type[Resource]
    spec: IOSpec

    def __init__(self, port_name: str, resource_type: type[Resource], spec: IOSpec) -> None:
        self.port_name = port_name
        self.resource_type = resource_type
        self.excepted_types = spec
        super().__init__(
            detail=GWSException.RESOURCE_NOT_COMPATIBLE.value,
            unique_code=GWSException.RESOURCE_NOT_COMPATIBLE.name,
            detail_args={
                "port": port_name,
                "resource_type": resource_type,
                "expected_types": spec.resource_types,
            },
        )


class MissingInputResourcesException(BadRequestException):
    """Raised when 1 or more input resources was not provided

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    port_names: list[str]

    def __init__(self, port_names: list[str]) -> None:
        self.port_names = port_names
        super().__init__(
            detail=GWSException.MISSING_INPUT_RESOURCES.value,
            unique_code=GWSException.MISSING_INPUT_RESOURCES.name,
            detail_args={"port_names": ",".join(port_names)},
        )


class ImcompatiblePortsException(BadRequestException):
    """Exception raised when trying to create a Connector but the port a imcompatible

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
            detail_args={
                "out_port_name": out_port.name,
                "out_port_types": out_port.resource_spec.get_resources_human_names(),
                "in_port_name": in_port.name,
                "in_port_types": in_port.resource_spec.get_resources_human_names(),
            },
        )


class InvalidInputsException(Exception):
    pass


class InvalidOutputsException(Exception):
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
#             detail_args={"out_port_name": out_port.name, "out_port_types": out_port.resource_spec.resource_types,
#                          "in_port_name": in_port.name, "in_port_types": in_port.resource_spec.resource_types})


from typing import List, Type

from gws_core.core.exception.gws_exceptions import GWSException

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..resource.resource import Resource


class ResourceNotCompatibleException(BadRequestException):
    """Error raise when we try to set the port resource with an incompatible resource

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    port_name: str
    resource_type: Type[Resource]
    excepted_types: List[Type[Resource]]

    def __init__(self, port_name: str, resource_type: Type[Resource],  excepted_types: List[Type[Resource]]) -> None:
        self.port_name = port_name
        self.resource_type = resource_type
        self.excepted_types = excepted_types
        super().__init__(
            detail=GWSException.RESOURCE_NOT_COMPATIBLE.value,
            unique_code=GWSException.RESOURCE_NOT_COMPATIBLE.name,
            detail_args={"port": port_name, "resource_type": resource_type, "expected_types": excepted_types})


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



from typing import Dict, Iterable, List, Type, TypedDict, Union

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..resource.resource import Resource

IOSpec = Union[Type[Resource], Iterable[Type[Resource]]]
IOSpecs = Dict[str, IOSpec]


class PortResourceDict(TypedDict):
    uri: str
    typing_name: str


class PortDict(TypedDict):
    resource: PortResourceDict
    specs: List[str]  # list of supported resource typing names


IODict = Dict[str, PortDict]


class IOSpecsHelper():
    """Class containing only class method to simplify IOSpecs management
    """

    @classmethod
    def io_spec_to_resource_types(cls, io_spec: IOSpec) -> List[Type[Resource]]:
        """Convert a IOSpec to list of resources
        It also checks that the type is a Resource
        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[Type[Resource]]
        """

        # if the type is a Union or Optional (equivalient to Union[x, None])
        if hasattr(io_spec, "__args__") and isinstance(io_spec.__args__, tuple):
            io_spec = io_spec.__args__
        elif not isinstance(io_spec, Iterable):
            io_spec = [io_spec]

        resource_types: List[Type[Resource], None] = []

        for res_t in io_spec:
            # convert the NoneType to None
            if res_t is type(None):
                resource_types.append(None)
                continue

            # check that the type is a resource Resource
            if res_t is not None and not issubclass(res_t, Resource):
                raise BadRequestException(
                    "Invalid port specs. The resources types must refer to a subclass of Resource")
            resource_types.append(res_t)

        return resource_types

    @classmethod
    def resource_type_is_compatible(cls, resource_type: Type[Resource], expected_types: List[Type[Resource]],
                                    exclude_none: bool = False) -> bool:
        """Check if a resource type is compataible with excpeted types

        :param resource_type: type to check
        :type resource_type: Type[Resource]
        :param expected_types: [description]
        :type expected_types: List[Type[Resource]]
        :param exclude_none: if True the None are considere incompatible
        :type exclude_none: bool, optional
        :return: [description]
        :rtype: bool
        """

        # check that the resource type is is subclass of one of the port resources types
        for expected_type in expected_types:
            if resource_type is None and exclude_none:
                continue

            if issubclass(resource_type, expected_type):
                return True

        return False

    @classmethod
    def resources_types_are_compatible(
            cls, resources_types_1: List[Type[Resource]],
            resources_types_2: List[Type[Resource]]) -> bool:

        for resource_type in resources_types_1:
            # compare the type and exclude the None
            if cls.resource_type_is_compatible(resource_type, resources_types_2, True):
                return True

        return False

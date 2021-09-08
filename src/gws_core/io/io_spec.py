# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Iterable, List, Type, Union, get_args

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..resource.resource import Resource
from .io_types import SubClasses

IOSpec = Union[Type[Resource], Iterable[Type[Resource]], SubClasses[Resource]]
IOSpecs = Dict[str, IOSpec]

PreProcessedResourceType = Union[Type[Resource], SubClasses[Resource], None]


class IOSpecClass:

    resource_spec: IOSpec = None

    def __init__(self, spec: IOSpec) -> None:
        self.resource_spec = spec

    def to_resource_types(self) -> List[PreProcessedResourceType]:
        return IOSpecsHelper.io_spec_to_resource_types(self.resource_spec)

    def is_compatible_with_spec(self, spec: 'IOSpecClass') -> bool:
        return IOSpecsHelper.resources_types_are_compatible(self.to_resource_types(), spec.to_resource_types())

    def is_compatible_with_type(self, resource_type: Type[Resource]) -> bool:
        return IOSpecsHelper.resource_type_is_compatible(
            resource_type=resource_type, expected_types=self.to_resource_types())

    def is_optional(self) -> bool:
        return None in self.to_resource_types()


class IOSpecsHelper():
    """Class containing only class method to simplify IOSpecs management
    """

    @classmethod
    def io_specs_to_resource_types(cls, io_specs: IOSpecs) -> Dict[str, List[Type[Resource]]]:
        """Convert all specs (IOSpecs) to list of resources

        :param io_specs: [description]
        :type io_specs: IOSpecs
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Dict[str, List[Type[Resource]]]
        """

        specs: Dict[str, List[Type[Resource]]] = {}
        for key, spec in io_specs.items():
            specs[key] = cls.io_spec_to_resource_types(spec)

        return specs

    @classmethod
    def io_spec_to_resource_types(cls, io_spec: IOSpec) -> List[PreProcessedResourceType]:
        """Convert a IOSpec to list of resources
        It also checks that the type is a Resource
        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[Type[Resource]]
        """

        if SubClasses.is_sub_class_type(io_spec):
            io_spec = [io_spec]
        # if the type is a Union or Optional (equivalient to Union[x, None])
        elif hasattr(io_spec, "__args__") and isinstance(io_spec.__args__, tuple):
            io_spec = get_args(io_spec)
        elif not isinstance(io_spec, Iterable):
            io_spec = [io_spec]

        resource_types: List[PreProcessedResourceType] = []

        for res_t in io_spec:
            # convert the NoneType to None
            if res_t is type(None) or res_t is None:
                resource_types.append(None)
                continue

            if SubClasses.is_sub_class_type(res_t):
                # Check that the type used in SubClass is a Resource
                if not issubclass(SubClasses.extract_type(res_t), Resource):
                    raise BadRequestException(
                        f"Invalid port specs. The type '{res_t}' used inside a SubClasses is not a resource")
            else:
                # check that the type is a Resource or a SubClasses
                if not issubclass(res_t, Resource):
                    raise BadRequestException(f"Invalid port specs. The type '{res_t}' is not a resource")
            resource_types.append(res_t)

        return resource_types

    @classmethod
    def resource_type_is_compatible(cls, resource_type: PreProcessedResourceType,
                                    expected_types: List[PreProcessedResourceType],
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

        # Handle the generic SubClasss
        if SubClasses.is_sub_class_type(resource_type):
            resource_type: Type[Resource] = SubClasses.extract_type(resource_type)
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return cls.resource_type_is_compatible(resource_type=resource_type, expected_types=expected_types,
                                                   exclude_none=exclude_none) or cls.resources_types_are_compatible(
                resources_types_1=expected_types, resources_types_2=[resource_type])

        # check that the resource type is is subclass of one of the port resources types
        for expected_type in expected_types:
            if resource_type is None and exclude_none:
                continue

            if issubclass(resource_type, expected_type):
                return True

        return False

    @classmethod
    def resources_types_are_compatible(
            cls, resources_types_1: List[PreProcessedResourceType],
            resources_types_2: List[PreProcessedResourceType]) -> bool:

        for resource_type in resources_types_1:
            # compare the type and exclude the None
            if cls.resource_type_is_compatible(resource_type, resources_types_2, True):
                return True

        return False

    @classmethod
    def io_specs_to_json(cls, io_specs: IOSpecs) -> Dict[str, List[str]]:
        """to_json method for IOSpecs
        """

        # Convert the specs to a list of resources types
        specs: Dict[str, List[Type[Resource]]] = cls.io_specs_to_resource_types(io_specs)

        _json:  Dict[str, List[str]] = {}
        for key, spec in specs.items():
            resources_json: List[str] = []

            for resource_type in spec:
                if resource_type is None:
                    resources_json.append(None)
                else:
                    # set the resource typing name as spec
                    resources_json.append(resource_type._typing_name)

            _json[key] = resources_json

        return _json

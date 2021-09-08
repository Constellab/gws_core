# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Iterable, List, Type, Union, get_args

from gws_core.io import io_types

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..resource.resource import Resource
from .io_types import (OptionalIn, SkippableIn, SpecialTypeIO, SubClassesOut,
                       UnmodifiedOut)

ResourceType = Type[Resource]


InputSpecType = Type[Union[Resource, OptionalIn[Resource], SkippableIn[Resource]]]
InputSpec = Union[InputSpecType, Iterable[InputSpecType]]
InputSpecs = Dict[str, InputSpec]

OutputSpecType = Type[Union[Resource, SubClassesOut[Resource], UnmodifiedOut[Resource]]]
OutputSpec = Union[OutputSpecType, Iterable[OutputSpecType]]
OutputSpecs = Dict[str, OutputSpec]

IOSpecType = Union[InputSpecType, OutputSpecType]
IOSpec = Union[IOSpecType, Iterable[IOSpecType]]
IOSpecs = Dict[str, IOSpec]


class IOSpecClass:

    resource_spec: IOSpec = None

    def __init__(self, spec: IOSpec) -> None:
        self.resource_spec = spec

    def to_resource_types(self) -> List[ResourceType]:
        return IOSpecsHelper.io_spec_to_resource_types(self.resource_spec)

    def is_compatible_with_spec(self, spec: 'IOSpecClass') -> bool:
        return IOSpecsHelper.specs_are_compatible(self.resource_spec, spec.resource_spec)

    def is_compatible_with_type(self, resource_type: Type[Resource]) -> bool:
        return IOSpecsHelper.spec_is_compatible(
            io_type=resource_type, expected_types=self.to_resource_types())

    def is_optional(self) -> bool:
        return OptionalIn.is_class(self.resource_spec) or None in self.to_resource_types()

    def is_unmodified_out(self) -> bool:
        return UnmodifiedOut.is_class(self.resource_spec)

    def is_skippable_in(self) -> bool:
        return SkippableIn.is_class(self.resource_spec)


class IOSpecsHelper():
    """Class containing only class method to simplify IOSpecs management
    """

    @classmethod
    def io_specs_to_resource_types(cls, io_specs: IOSpecs) -> Dict[str, List[ResourceType]]:
        """Convert all specs (IOSpecs) to list of resources

        :param io_specs: [description]
        :type io_specs: IOSpecs
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Dict[str, List[Type[Resource]]]
        """

        specs: Dict[str, List[ResourceType]] = {}
        for key, spec in io_specs.items():
            specs[key] = cls.io_spec_to_resource_types(spec)

        return specs

    @classmethod
    def io_spec_to_resource_types(cls, io_spec: IOSpec) -> List[ResourceType]:
        """Convert a IOSpec to list of resources types
        It also checks that the type is a Resource
        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[Type[Resource]]
        """

        io_spec_list: List[IOSpecType] = cls.io_spec_to_list(io_spec)

        resource_types: List[ResourceType] = []

        for io_spec in io_spec_list:
            # convert the NoneType to None
            if io_spec is type(None) or io_spec is None:
                resource_types.append(None)
                continue

            if SpecialTypeIO.is_class(io_spec):
                # Check that the type used in SubClass is a Resource
                if not issubclass(SpecialTypeIO.extract_type(io_spec), Resource):
                    raise BadRequestException(
                        f"Invalid port specs. The type '{io_spec}' used inside the special type '{io_spec}'' is not a resource")
                resource_types.append(SpecialTypeIO.extract_type(io_spec))
            else:
                # check that the type is a Resource or a SubClasses
                if not issubclass(io_spec, Resource):
                    raise BadRequestException(f"Invalid port specs. The type '{io_spec}' is not a resource")
                resource_types.append(io_spec)

        return resource_types

    @classmethod
    def io_spec_to_list(cls, io_spec: IOSpec) -> List[IOSpecType]:
        """Convert IOSpec to a list of types

        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[IOSpecType]
        """

        if SpecialTypeIO.is_class(io_spec):
            return [io_spec]
        # if the type is a Union or Optional (equivalient to Union[x, None])
        elif hasattr(io_spec, "__args__") and isinstance(io_spec.__args__, tuple):
            return get_args(io_spec)
        elif not isinstance(io_spec, Iterable):
            return [io_spec]

        return io_spec

    @classmethod
    def spec_is_compatible(cls, io_type: IOSpecType,
                           expected_types: IOSpec,
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
        if SubClassesOut.is_class(io_type):
            resource_type: Type[Resource] = SubClassesOut.extract_type(io_type)
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return cls.spec_is_compatible(io_type=resource_type, expected_types=expected_types,
                                          exclude_none=exclude_none) or cls.specs_are_compatible(
                output_specs_1=expected_types, input_specs_2=[resource_type])

        # Convert the io_type to resource type
        resource_type: Type[Resource]
        if SpecialTypeIO.is_class(io_type):
            resource_type = SpecialTypeIO.extract_type(io_type)
        else:
            resource_type = io_type

        expected_r_types: List[ResourceType] = cls.io_spec_to_resource_types(expected_types)
        # check that the resource type is a subclass of one of the port resources types
        for expected_type in expected_r_types:
            if resource_type is None and exclude_none:
                continue

            if issubclass(resource_type, expected_type):
                return True

        return False

    @classmethod
    def specs_are_compatible(
            cls, output_specs_1: IOSpec,
            input_specs_2: IOSpec) -> bool:

        output_spec_list: List[IOSpecType] = cls.io_spec_to_list(output_specs_1)

        for output_spec in output_spec_list:
            # compare the type and exclude the None
            if cls.spec_is_compatible(output_spec, input_specs_2, True):
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

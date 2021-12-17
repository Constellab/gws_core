# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from collections.abc import Iterable as IterableClass
from typing import Dict, Iterable, List, Literal, Type, Union, get_args

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.utils.utils import Utils
from ..resource.resource import Resource
from ..task.task_io import TaskInputs
from .io_special_type import (ConstantOut, OptionalIn, SkippableIn,
                              SpecialTypeIn, SpecialTypeIO, SpecialTypeOut,
                              TypeIO, TypeIODict)

ResourceType = Type[Resource]

# Specs for a task Input, a resource type, a list of resource type or a SpecialTypeIn (check SpecialTypeIn for more information)
InputSpec = Union[ResourceType, Iterable[ResourceType], SpecialTypeIn]
InputSpecs = Dict[str, InputSpec]

# Specs for a task Output, a resource type, a list of resource type or a SpecialTypeOut (check SpecialTypeOut for more information)
OutputSpec = Union[ResourceType, Iterable[ResourceType], SpecialTypeOut]
OutputSpecs = Dict[str, OutputSpec]

IOSpec = Union[InputSpec, OutputSpec, TypeIO]
IOSpecs = Dict[str, IOSpec]


class IOSpecClass:

    type_io: TypeIO

    resource_spec: IOSpec = None

    def __init__(self, spec: IOSpec) -> None:

        if isinstance(spec, TypeIO):
            self.type_io = spec
        else:
            self.type_io = TypeIO(spec)

    def to_resource_types(self) -> Iterable[ResourceType]:
        return IOSpecsHelper.io_spec_to_resource_types(self.type_io)

    def is_compatible_with_spec(self, spec: 'IOSpecClass') -> bool:
        return IOSpecsHelper.specs_are_compatible(self.type_io, spec.type_io)

    def is_compatible_with_type(self, resource_type: Type[Resource]) -> bool:
        return IOSpecsHelper.spec_is_compatible(
            io_type=resource_type, expected_types=self.to_resource_types())

    def is_optional(self) -> bool:
        return isinstance(self.type_io, OptionalIn) or None in self.to_resource_types()

    def is_constant_out(self) -> bool:
        return isinstance(self.type_io, ConstantOut)

    def is_skippable_in(self) -> bool:
        return isinstance(self.type_io, SkippableIn)

    def to_json(self) -> TypeIODict:
        return self.type_io.to_json()

    @classmethod
    def from_json(cls, json_: TypeIODict) -> 'IOSpecClass':
        return IOSpecClass(TypeIO.from_json(json_))


class IOSpecsHelper():
    """Class containing only class method to simplify IOSpecs management
    """

    @classmethod
    def io_specs_to_resource_types(cls, io_specs: IOSpecs) -> Dict[str, Iterable[ResourceType]]:
        """Convert all specs (IOSpecs) to list of resources

        :param io_specs: [description]
        :type io_specs: IOSpecs
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Dict[str, List[Type[Resource]]]
        """

        specs: Dict[str, Iterable[ResourceType]] = {}
        for key, spec in io_specs.items():
            specs[key] = cls.io_spec_to_resource_types(spec)

        return specs

    @classmethod
    def io_spec_to_resource_types(cls, io_spec: IOSpec) -> Iterable[ResourceType]:
        """Convert a IOSpec to list of resources types
        It also checks that the type is a Resource
        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[Type[Resource]]
        """

        io_spec_list: Iterable[IOSpec] = cls.io_spec_to_list(io_spec)

        resource_types: List[ResourceType] = []

        for spec in io_spec_list:
            # convert the NoneType to None
            if spec is type(None) or spec is None:
                resource_types.append(None)
                continue

            if isinstance(spec, TypeIO):
                spec.check_resource_types()
                resource_types.extend(spec.resource_types)
            else:
                # check that the type is a Resource or a SubClasses
                if not Utils.issubclass(spec, Resource):
                    raise BadRequestException(f"Invalid port specs. The type '{spec}' is not a resource")
                resource_types.append(spec)

        return resource_types

    @classmethod
    def io_spec_to_list(cls, io_spec: IOSpec) -> Iterable[IOSpec]:
        """Convert IOSpec to a list of types

        :param io_spec: [description]
        :type io_spec: IOSpec
        :return: [description]
        :rtype: List[IOSpecType]
        """

        if isinstance(io_spec, TypeIO):
            return [io_spec]
        # if the type is a Union or Optional (equivalient to Union[x, None])
        elif hasattr(io_spec, "__args__") and isinstance(io_spec.__args__, tuple):
            return get_args(io_spec)
        elif not isinstance(io_spec, IterableClass):
            return [io_spec]

        return io_spec

    @classmethod
    def spec_is_compatible(cls, io_type: IOSpec,
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
        if isinstance(io_type, SpecialTypeOut) and io_type.sub_class:
            resource_types_1: Iterable[ResourceType] = io_type.resource_types
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return cls.specs_are_compatible(
                output_specs_1=resource_types_1, input_specs_2=expected_types) or cls.specs_are_compatible(
                output_specs_1=expected_types, input_specs_2=resource_types_1)

        # Convert the io_type to resource types
        resource_types: Iterable[ResourceType] = cls.io_spec_to_resource_types(io_type)

        expected_r_types: Iterable[ResourceType] = cls.io_spec_to_resource_types(expected_types)

        return cls._resource_types_are_compatible(
            resource_types=resource_types, expected_types=expected_r_types, exclude_none=exclude_none)

    @classmethod
    def _resource_types_are_compatible(cls, resource_types: Iterable[Type[Resource]],
                                       expected_types: Iterable[Type[Resource]],
                                       exclude_none: bool = False) -> bool:

        for resource_type in resource_types:
            if cls._resource_types_is_compatible(
                    resource_type=resource_type, expected_types=expected_types, exclude_none=exclude_none):
                return True

        return False

    @classmethod
    def _resource_types_is_compatible(cls, resource_type: Type[Resource],
                                      expected_types: Iterable[Type[Resource]],
                                      exclude_none: bool = False) -> bool:

        if resource_type is None and exclude_none:
            return False

        # check that the resource type is a subclass of one of the port resources types
        for expected_type in expected_types:
            if issubclass(resource_type, expected_type):
                return True

        return False

    @classmethod
    def specs_are_compatible(
            cls, output_specs_1: IOSpec,
            input_specs_2: IOSpec) -> bool:

        output_spec_list: Iterable[IOSpec] = cls.io_spec_to_list(output_specs_1)

        for output_spec in output_spec_list:
            # compare the type and exclude the None
            if cls.spec_is_compatible(output_spec, input_specs_2, True):
                return True

        return False

    @classmethod
    def io_specs_to_json(cls, io_specs: IOSpecs) -> Dict[str, TypeIODict]:
        """to_json method for IOSpecs
        """

        json_:  Dict[str, TypeIODict] = {}
        for key, spec in io_specs.items():
            json_[key] = IOSpecClass(spec).to_json()
        return json_

    @classmethod
    def check_input_specs(cls, input_specs: InputSpecs) -> None:
        """Method to verify that input specs are valid
        """
        cls._check_io_spec_param(input_specs, 'input', SpecialTypeIn)

    @classmethod
    def check_output_specs(cls, output_specs: OutputSpecs) -> None:
        """Method to verify that output specs are valid
        """
        cls._check_io_spec_param(output_specs, 'output', SpecialTypeOut)

    @classmethod
    def _check_io_spec_param(cls, io_specs: IOSpecs,
                             param_type: Literal['input', 'output'], special_type: Type[SpecialTypeIO]) -> None:
        if not io_specs:
            return

        if not isinstance(io_specs, dict):
            raise Exception("The specs must be a dictionary")

        for key, item in io_specs.items():
            params: Iterable[ResourceType]

            if isinstance(item, special_type):
                params = item.resource_types
            elif not isinstance(item, IterableClass):
                params = [item]
            else:
                params = item

            for param in params:
                if param is not None and not Utils.issubclass(param, Resource):
                    raise Exception(
                        f"The {param_type} param of spec '{key}' is invalid. Expected a resource type, got {str(param)}")

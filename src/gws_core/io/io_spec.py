# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractmethod
from collections.abc import Iterable as IterableClass
from typing import Iterable, List, Optional, Tuple, Type, Union

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_dict import TypingRefDTO

from ..model.typing_manager import TypingManager
from ..resource.resource import Resource
from .io_validator import IOValidator

ResourceType = Type[Resource]
ResourceTypes = Union[ResourceType, Iterable[ResourceType]]


class IOSpecDTO(BaseModelDTO):
    resource_types: List[TypingRefDTO]
    human_name: Optional[str]
    short_description: Optional[str]
    is_optional: bool
    sub_class: Optional[bool] = None
    is_constant: Optional[bool] = None


class IOSpec:
    resource_types: List[ResourceType]

    # Human readable name of the param, showed in the interface
    human_name: Optional[str]

    # Description of the param, showed in the interface
    short_description: Optional[str]

    is_optional: bool = False

    validators: List[IOValidator] = []

    _name: str = "IOSpec"   # unique name to distinguish the types, do not modify

    def __init__(self, resource_types: ResourceTypes, is_optional: bool = False, human_name: Optional[str] = None,
                 short_description: Optional[str] = None,
                 validators: List[IOValidator] = None) -> None:
        """[summary]

        :param resource_types: type of supported resource or resources
        :type resource_types: Type[Union[Resource, Iterable[Resource]]]
        """

        self.resource_types = []
        if not isinstance(resource_types, IterableClass):
            self.resource_types.append(resource_types)
        else:
            for r_type in resource_types:
                self.resource_types.append(r_type)

        self.is_optional = is_optional

        self.check_resource_types()

        default_type = self.get_default_resource_type()

        # set the human name with a default value
        if human_name is not None:
            self.human_name = human_name
        else:
            self.human_name = default_type._human_name

        # set the short description with a default value
        if short_description is not None:
            self.short_description = short_description
        else:
            self.short_description = default_type._short_description

        self.validators = validators or []

    def check_resource_types(self):
        for resource_type in self.resource_types:
            if resource_type is None:
                raise Exception("Resource type can't be None, please set optional parameter to True instead")

            if not Utils.issubclass(resource_type, Resource):
                raise Exception(
                    f"Invalid port specs. The type '{resource_type}' used inside the type '{type(self).__name__}' is not a resource")

    def is_compatible_with_in_spec(self, in_spec: 'IOSpec') -> bool:
        # Handle the generic SubClasss
        if self.is_subclass_out():
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return self._resource_types_are_compatible(
                resource_types=self.resource_types, expected_types=in_spec.resource_types) or self._resource_types_are_compatible(
                resource_types=in_spec.resource_types, expected_types=self.resource_types)

        return self._resource_types_are_compatible(
            resource_types=self.resource_types, expected_types=in_spec.resource_types)

    def is_compatible_with_resource_type(self, resource_type: Type[Resource]) -> bool:
        return self._resource_types_are_compatible(resource_types=[resource_type], expected_types=self.resource_types)

    def is_compatible_with_resource_types(self, resource_types: Iterable[Type[Resource]]) -> bool:
        """return True if one of the resource_types is compatible with the this spec
        """
        return self._resource_types_are_compatible(resource_types=resource_types, expected_types=self.resource_types)

    @abstractmethod
    def is_constant_out(self) -> bool:
        pass

    @abstractmethod
    def is_subclass_out(self) -> bool:
        pass

    def get_default_resource_type(self) -> Type[Resource]:
        """return the first default type
        """
        return self.resource_types[0]

    def get_resource_type_tuples(self) -> Tuple[Type[Resource]]:
        return tuple(self.resource_types)

    def get_resources_human_names(self) -> str:
        list_str = [(resource_type._human_name if resource_type else 'None')
                    for resource_type in self.resource_types]

        if len(list_str) == 1:
            return list_str[0]
        else:
            return ', '.join(list_str)

    def validate_resource(self, resource: Resource) -> None:
        """Validate a resource with the validators
        """
        if resource is None:
            return
        for validator in self.validators:
            validator.check_type(resource)
            validator.validate(resource)

    @classmethod
    def _resource_types_are_compatible(cls, resource_types: Iterable[Type[Resource]],
                                       expected_types: Iterable[Type[Resource]]) -> bool:

        for resource_type in resource_types:
            if cls._resource_types_is_compatible(
                    resource_type=resource_type, expected_types=expected_types):
                return True

        return False

    @classmethod
    def _resource_types_is_compatible(cls, resource_type: Type[Resource],
                                      expected_types: Iterable[Type[Resource]]) -> bool:

        # check that the resource type is a subclass of one of the port resources types
        for expected_type in expected_types:
            if issubclass(resource_type, expected_type):
                return True

        return False

    @classmethod
    def _resource_types_is_type(cls, resource_type: Type[Resource],
                                expected_types: Iterable[Type[Resource]]) -> bool:
        return resource_type in expected_types

    def to_dto(self) -> IOSpecDTO:
        spec_dto = IOSpecDTO(
            resource_types=[],
            is_optional=self.is_optional,
            human_name=self.human_name,
            short_description=self.short_description,
        )

        for resource_type in self.resource_types:
            typing = TypingManager.get_typing_from_name_and_check(
                resource_type._typing_name)

            spec_dto.resource_types.append(TypingRefDTO(
                typing_name=typing.typing_name,
                brick_version=str(BrickHelper.get_brick_version(typing.brick)),
                human_name=typing.human_name
            ))
        return spec_dto

    @classmethod
    def from_dto(cls, dto: IOSpecDTO) -> 'IOSpec':

        resource_types: List[ResourceType] = []

        # retrieve all the resource type from the json specs
        for spec_dto in dto.resource_types:
            resource_type: ResourceType = TypingManager.get_type_from_name(
                spec_dto.typing_name)

            if resource_type is None:
                raise Exception(
                    f"[IOSpec] Invalid resource type '{spec_dto.typing_name}'")
            resource_types.append(resource_type)

        io_spec: IOSpec = cls(resource_types=resource_types, is_optional=dto.is_optional,
                              human_name=dto.human_name,
                              short_description=dto.short_description,)
        return io_spec


class InputSpec(IOSpec):
    """ Spec for an input task port
    """
    _name: str = "InputSpec"

    def __init__(self, resource_types: ResourceTypes,
                 is_optional: bool = False,
                 is_skippable: bool = False,
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None,
                 validators: List[IOValidator] = None) -> None:
        """_summary_

        :param resource_types: _description_
        :type resource_types: ResourceTypes
        :param is_optional: this input might not be connected to another task output and the task will still be executed.
                      If the input is connected, the system will wait for the input to be provided before running the task.
                      Also tells that None value is allowed as input.  , defaults to False
        :type is_optional: bool, optional
        :param is_skippable DEPRECATED, use is_optional instead.
        :type is_skippable: bool, optional
        :param human_name: _description_, defaults to None
        :type human_name: Optional[str], optional
        :param short_description: _description_, defaults to None
        :type short_description: Optional[str], optional
        """
        # if the input is skippable force it to be optional
        if is_skippable:
            Logger.warning(
                '[DEPRECATED] is_skippable is deprecated, use is_optional instead')
            is_optional = True

        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description,
                         validators=validators)

    def is_constant_out(self) -> bool:
        return False

    def is_subclass_out(self) -> bool:
        return False


class OutputSpec(IOSpec):
    """ Spec for an output task port
    """
    _name: str = "OutputSpec"

    _sub_class: bool
    _is_constant: bool

    def __init__(self, resource_types: ResourceTypes,
                 is_optional: bool = False,
                 sub_class: bool = False,
                 is_constant: bool = False,
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None,
                 validators: List[IOValidator] = None) -> None:
        """_summary_

        :param resource_types: _description_
        :type resource_types: ResourceTypes
        :param is_optional: tell that this output may return None or not being provided, defaults to False
        :type is_optional: bool, optional
        :param sub_class: When true, it tells that the resource_types
                are compatible with any child class of the provided resource type, defaults to False
        :param is_constant: When true, this tells the system that the output resource was not modified from the input resource
              and it does not need to create a new resource after the task, defaults to False
        :param human_name: _description_, defaults to None
        :type human_name: Optional[str], optional
        :param short_description: _description_, defaults to None
        :type short_description: Optional[str], optional
        """

        super().__init__(resource_types=resource_types, is_optional=is_optional,
                         human_name=human_name, short_description=short_description,
                         validators=validators)
        self._sub_class = sub_class
        self._is_constant = is_constant

    def is_constant_out(self) -> bool:
        return self._is_constant

    def is_subclass_out(self) -> bool:
        return self._sub_class

    def to_dto(self) -> IOSpecDTO:
        spec_dto = super().to_dto()

        spec_dto.sub_class = self._sub_class
        spec_dto.is_constant = self._is_constant

        return spec_dto

    @classmethod
    def from_dto(cls, dto: IOSpecDTO) -> 'OutputSpec':
        output_spec: OutputSpec = super().from_dto(dto)

        output_spec._sub_class = dto.sub_class or False
        output_spec._is_constant = dto.is_constant or False

        return output_spec

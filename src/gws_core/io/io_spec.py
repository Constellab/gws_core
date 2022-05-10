# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from collections.abc import Iterable as IterableClass
from typing import (Any, Dict, Iterable, List, Optional, Tuple, Type,
                    TypedDict, Union)

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.utils import Utils

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..resource.resource import Resource

ResourceType = Type[Resource]
ResourceTypes = Union[ResourceType, Iterable[ResourceType]]


class ResourceTypeJson(TypedDict):
    typing_name: str
    human_name: str
    short_description: str


class IOSpecDict(TypedDict):
    io_spec: str
    resource_types: List[ResourceTypeJson]
    data: Dict[str, Any]


class IOSpec:
    resource_types: List[ResourceType]

    # Human readable name of the param, showed in the interface
    human_name: Optional[str]

    # Description of the param, showed in the interface
    short_description: Optional[str]

    _name: str = "IOSpec"   # unique name to distinguish the types, do not modify

    def __init__(self, resource_types: ResourceTypes, human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
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
        self.check_resource_types()

        # set the human name with a default value
        if human_name is not None:
            self.human_name = human_name
        else:
            self.human_name = self.get_default_resource_type()._human_name

        # set the short description with a default value
        if short_description is not None:
            self.short_description = short_description
        else:
            self.short_description = self.get_default_resource_type()._short_description

    def check_resource_types(self):
        for resource_type in self.resource_types:
            if not Utils.issubclass(resource_type, Resource):
                raise BadRequestException(
                    f"Invalid port specs. The type '{resource_type}' used inside the type '{type(self).__name__}' is not a resource")

    def is_compatible_with_in_spec(self, in_spec: 'IOSpec',
                                   exclude_none: bool = False) -> bool:
        # Handle the generic SubClasss
        if self.is_subclass_out():
            # check if type inside the SubClass is compatible with expected type
            # if not check if one of the expected type is compatible with SubClass
            return self._resource_types_are_compatible(
                resource_types=self.resource_types, expected_types=in_spec.resource_types, exclude_none=True) or self._resource_types_are_compatible(
                resource_types=in_spec.resource_types, expected_types=self.resource_types, exclude_none=True)

        return self._resource_types_are_compatible(
            resource_types=self.resource_types, expected_types=in_spec.resource_types, exclude_none=exclude_none)

    def is_compatible_with_resource_type(self, resource_type: Type[Resource]) -> bool:
        return self._resource_types_are_compatible(resource_types=[resource_type], expected_types=self.resource_types)

    def is_optional(self) -> bool:
        return isinstance(self, OptionalIn) or None in self.resource_types

    def is_constant_out(self) -> bool:
        return isinstance(self, ConstantOut)

    def is_skippable_in(self) -> bool:
        return isinstance(self, SkippableIn)

    def is_subclass_out(self) -> bool:
        return isinstance(self, OutputSpec) and self.sub_class

    def get_default_resource_type(self) -> Type[Resource]:
        """return the first default type
        """
        return self.resource_types[0]

    def get_resource_type_tuples(self) -> Tuple[Type[Resource]]:
        return tuple(self.resource_types)

    def get_resources_human_names(self) -> str:
        list_str = [(resource_type._human_name if resource_type else 'None') for resource_type in self.resource_types]

        if len(list_str) == 1:
            return list_str[0]
        else:
            return ', '.join(list_str)

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

    def to_json(self) -> IOSpecDict:
        json_: IOSpecDict = {"io_spec": self._name, "resource_types": [], "data": {},
                             "human_name": self.human_name, "short_description": self.short_description}
        for resource_type in self.resource_types:
            if resource_type is None:
                json_["resource_types"].append({"typing_name": None, "human_name": None, 'short_description': None,
                                                "brick_name": None, "unique_name": None, 'brick_version': None})
            else:
                typing = TypingManager.get_typing_from_name(resource_type._typing_name)
                json_["resource_types"].append(
                    {"typing_name": typing.typing_name, "human_name": typing.human_name,
                     "short_description": typing.short_description, "brick_name": typing.brick,
                     "unique_name": typing.model_name, "brick_version": str(BrickHelper.get_brick_version(typing.brick))})
        return json_

    @classmethod
    def from_json(cls, json_: IOSpecDict) -> 'IOSpec':
        type_: Type[IOSpec] = cls._get_type_from_name(json_['io_spec'])

        resource_types: List[ResourceType] = []

        # retrieve all the resource type from the json specs
        for spec_json in json_['resource_types']:
            resource_types.append(TypingManager.get_type_from_name(spec_json['typing_name']))

        return type_(resource_types=resource_types, **json_['data'])

    @classmethod
    def _get_type_from_name(cls, type_name: str) -> Type['IOSpec']:
        if type_name == 'IOSpec':
            return IOSpec
        elif type_name == 'InputSpec':
            return InputSpec
        elif type_name == 'OutputSpec':
            return OutputSpec
        elif type_name == 'OptionalIn':
            return OptionalIn
        elif type_name == 'SkippableIn':
            return SkippableIn
        elif type_name == 'ConstantOut':
            return ConstantOut
        else:
            raise Exception(f"[TypeIO] The type name {type_name} does not correspond to a type")


class InputSpec(IOSpec):
    """ Spec for an input task port
    """
    _name: str = "InputSpec"


class OutputSpec(IOSpec):
    """ Spec for an output task port
    """
    _name: str = "OutputSpec"

    sub_class: bool

    def __init__(self, resource_types: ResourceTypes, sub_class: bool = False,
                 human_name: Optional[str] = None,
                 short_description: Optional[str] = None) -> None:
        """[summary]

        :param resource_types: [description]
        :type resource_types: Type[Union[Resource, Iterable[Resource]]]
        :param sub_class: When true, it tells that the resource_types
                are compatible with any child class of the provided resource type, defaults to False
        :type sub_class: bool, optional
        """
        super().__init__(resource_types=resource_types, human_name=human_name, short_description=short_description)
        self.sub_class = sub_class

    # Add the sub class attribute
    def to_json(self) -> IOSpecDict:
        json_ = super().to_json()
        json_['data']["sub_class"] = self.sub_class

        return json_


class OptionalIn(InputSpec):
    """Special type to use in Input specs
    This type tell the system that the input is optional.
    The input can be not connected and the task will still run (the input value will then be None)
    If the input is connected, the task will wait for the resource to run himself (this is the difference from SkippableIn)
    """

    _name: str = 'OptionalIn'


class SkippableIn(OptionalIn):
    """Special type to use in Input specs
    This type tell the system that the input is skippable. This mean that the task can be called
    even if this input was connected and the value no provided.
    With this you can run your task even if the input vaue was not received
    //!\\ WARNING If an input is skipped, the input is not set, the inputs['name'] will raise a KeyError exception (different from None)

    Has no effect when there is only one input

    """

    _name: str = 'SkippableIn'


class ConstantOut(OutputSpec):
    """Special type to use in Output specs
    This type tells the system that the output resource was not modified from the input resource
    and it does not need to create a new resource after the task
    """

    _name: str = 'ConstantOut'

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from collections.abc import Iterable as IterableClass
from typing import Any, Dict, Iterable, List, Type, TypedDict, Union

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


class TypeIODict(TypedDict):
    type_io: str
    resource_types: List[ResourceTypeJson]
    data: Dict[str, Any]


class TypeIO:
    resource_types: List[ResourceType]

    _name: str = "TypeIO"   # unique name to distinguish the types, do not modify

    def __init__(self, resource_types: ResourceTypes) -> None:
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

    def check_resource_types(self):
        for resource_type in self.resource_types:
            if not issubclass(resource_type, Resource):
                raise BadRequestException(
                    f"Invalid port specs. The type '{resource_type}' used inside the special type '{type(self).__name__}' is not a resource")

    def to_json(self) -> TypeIODict:
        json_: TypeIODict = {"type_io": self._name, "resource_types": [], "data": {}}
        for resource_type in self.resource_types:
            if resource_type is None:
                json_["resource_types"].append({"typing_name": None, "human_name": None, 'short_description': None})
            else:
                json_["resource_types"].append(
                    {"typing_name": resource_type._typing_name, "human_name": resource_type._human_name,
                     'short_description': resource_type._short_description})
        return json_

    @classmethod
    def from_json(cls, json_: TypeIODict) -> 'TypeIO':
        type_: Type[TypeIO] = cls._get_type_from_name(json_['type_io'])

        resource_types: List[ResourceType] = []

        # retrieve all the resource type from the json specs
        for spec_json in json_['resource_types']:
            resource_types.append(TypingManager.get_type_from_name(spec_json['typing_name']))

        return type_(resource_types=resource_types, **json_['data'])

    @classmethod
    def _get_type_from_name(cls, type_name: str) -> Type['TypeIO']:
        if type_name == 'TypeIO':
            return TypeIO
        elif type_name == 'SpecialTypeIO':
            return SpecialTypeIO
        elif type_name == 'SpecialTypeIn':
            return SpecialTypeIn
        elif type_name == 'OptionalIn':
            return OptionalIn
        elif type_name == 'SkippableIn':
            return SkippableIn
        elif type_name == 'SpecialTypeOut':
            return SpecialTypeOut
        elif type_name == 'ConstantOut':
            return ConstantOut
        else:
            raise Exception(f"[TypeIO] The type name {type_name} does not correspond to a type")


class SpecialTypeIO(TypeIO):
    """Special type for input or outputcheck sub classes to see the special types:
    """

    _name: str = 'SpecialTypeIO'


class SpecialTypeIn(SpecialTypeIO):
    """Special type for input check sub classes to see the special types:
     - SkippableIn
     - OptionalIn
    """

    _name: str = 'SpecialTypeIn'


class OptionalIn(SpecialTypeIn):
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


class SpecialTypeOut(SpecialTypeIO):
    """Special type for input check sub classes and constructor params to see the special types:
     - ConstantOut
    """

    sub_class: bool

    _name: str = 'SpecialTypeOut'

    def __init__(self, resource_types: ResourceTypes, sub_class: bool = False) -> None:
        """[summary]

        :param resource_types: [description]
        :type resource_types: Type[Union[Resource, Iterable[Resource]]]
        :param sub_class: When true, it tells that the resource_types
                are compatible with any child class of the provided resource type, defaults to False
        :type sub_class: bool, optional
        """
        super().__init__(resource_types=resource_types)
        self.sub_class = sub_class

    # Add the sub class attribute
    def to_json(self) -> TypeIODict:
        json_ = super().to_json()
        json_['data']["sub_class"] = self.sub_class

        return json_


class ConstantOut(SpecialTypeOut):
    """Special type to use in Output specs
    This type tells the system that the output resource was not modified from the input resource
    and it does not need to create a new resource after the task
    """

    _name: str = 'ConstantOut'

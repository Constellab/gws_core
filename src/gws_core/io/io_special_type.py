# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from collections.abc import Iterable as IterableClass
from typing import Iterable, List, Type, Union

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..resource.resource import Resource

ResourceType = Type[Resource]
ResourceTypes = Union[ResourceType, Iterable[ResourceType]]


class SpecialTypeIO:
    resource_types: List[ResourceType]

    def __init__(self, resource_types: ResourceTypes) -> None:
        """[summary]

        :param resource_types: type of supported resource or resources
        :type resource_types: Type[Union[Resource, Iterable[Resource]]]
        :param sub_class: When true, it tells that the resource_types
                are compatible with any child class of the provided resource type, defaults to False
        :type sub_class: bool, optional
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


class SpecialTypeIn(SpecialTypeIO):
    """Special type for input check sub classes to see the special types:
     - SkippableIn
     - OptionalIn
    """


class OptionalIn(SpecialTypeIn):
    """Special type to use in Input specs
    This type tell the system that the input is optional.
    The input can be not connected and the task will still run (the input value will then be None)
    If the input is connected, the task will wait for the resource to run himself (this is the difference from SkippableIn)
    This is equivalent to [Resource, None]
    """


class SkippableIn(OptionalIn):
    """Special type to use in Input specs
    This type tell the system that the input is skippable. This mean that the task can be called
    even if this input was connected and the value no provided.
    With this you can run your task even if the input vaue was not received
    //!\\ WARNING If an input is skipped, the input is not set, the inputs['name'] will raise a KeyError exception (different from None)

    Has no effect when there is only one input

    """


class SpecialTypeOut(SpecialTypeIO):
    """Special type for input check sub classes and constructor params to see the special types:
     - ConstantOut
    """

    sub_class: bool

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


class ConstantOut(SpecialTypeOut):
    """Special type to use in Output specs
    This type tells the system that the output resource was not modified from the input resource
    and it does not need to create a new resource after the task
    """

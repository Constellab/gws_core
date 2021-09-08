# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractclassmethod
from inspect import isclass
from typing import Any, Generic, Type, TypeVar, get_args

from gws_core.resource.resource import Resource

GenericResource = TypeVar('GenericResource', bound=Type[Resource])


class SpecialTypeIO(Generic[GenericResource]):

    @classmethod
    def is_class(cls, type_: Any) -> bool:
        return hasattr(
            type_, "__origin__") and isclass(
            type_.__origin__) and issubclass(
            type_.__origin__, cls._get_type())

    @classmethod
    def extract_type(cls, type_: Type['SpecialTypeIO']) -> Type[Resource]:
        return get_args(type_)[0]

    @classmethod
    def _get_type(cls) -> Type['SpecialTypeIO']:
        return SpecialTypeIO


class SubClassesOut(SpecialTypeIO, Generic[GenericResource]):
    """Special type to use in Output specs
    This type can only be used in a output spec and tell that this is compatible
    with any child type of the provided resource

    :param Generic: [description]
    :type Generic: [type]
    :return: [description]
    :rtype: [type]
    """

    @classmethod
    def _get_type(cls) -> Type['SpecialTypeIO']:
        return SubClassesOut


class UumodifiedOut(SpecialTypeIO, Generic[GenericResource]):
    """Special type to use in Output specs
    This type tell the system that the output resource was not modified from the input resource
    and it does not need to create a new resource

    :param SpecialTypeIO: [description]
    :type SpecialTypeIO: [type]
    :return: [description]
    :rtype: [type]
    """

    @classmethod
    def _get_type(cls) -> Type['SpecialTypeIO']:
        return UumodifiedOut


class SkippableIn(SpecialTypeIO, Generic[GenericResource]):
    """Special type to use in Input specs
    This type tell the system that the input is skippable. This mean that the process can be called
    even if this input was connected and the value no provided.
    With this you can run your process even if the input vaue was not received
    Has no effect when there is only one input

    :param SpecialTypeIO: [description]
    :type SpecialTypeIO: [type]
    :return: [description]
    :rtype: [type]
    """

    @classmethod
    def _get_type(cls) -> Type['SpecialTypeIO']:
        return SkippableIn

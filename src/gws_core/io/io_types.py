# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from inspect import isclass
from typing import Any, Generic, Type, TypeVar, get_args

from gws_core.resource.resource import Resource

T = TypeVar('T', bound=Resource)


class SubClasses(Generic[T]):
    """Special type to use in IOSpecs
    This type can only be used in a output spec and tell that this is compatible
    with any child type of the provided resource

    :param Generic: [description]
    :type Generic: [type]
    :return: [description]
    :rtype: [type]
    """

    @classmethod
    def is_sub_class_type(cls, type_: Type[Any]) -> bool:
        return hasattr(type_, "__origin__") and isclass(type_.__origin__) and issubclass(type_.__origin__, SubClasses)

    @classmethod
    def extract_type(cls, type_: Type['SubClasses']) -> Type[Resource]:
        return get_args(type_)[0]

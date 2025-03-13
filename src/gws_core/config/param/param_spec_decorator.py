
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, Type

if TYPE_CHECKING:
    from gws_core.config.param.param_spec import ParamSpec

# List all the param spec types annotated with the param_decorator
PARAM_SPEC_TYPES_LIST: List[Type[ParamSpec]] = []

SIMPLE_PARAM_SPEC_TYPES_LIST: List[Type[ParamSpec]] = []

NESTED_PARAM_SPEC_TYPES_LIST: List[Type[ParamSpec]] = []

LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST: List[Type[ParamSpec]] = []


class ParamaSpecType(Enum):
    SIMPLE = "simple"
    NESTED = "nested"
    LAB_SPECIFIC = "lab_specific"


def param_spec_decorator(type_: ParamaSpecType = ParamaSpecType.SIMPLE):
    """Decorator of ParamSpec class to add it to the list of param spec types
    """
    def decorator(param_class: Type[ParamSpec]):
        from gws_core.config.param.param_spec import ParamSpec

        if not issubclass(param_class, ParamSpec):
            raise Exception("The param decorator can only be used on a ParamSpec child class")
        PARAM_SPEC_TYPES_LIST.append(param_class)
        if type_ == ParamaSpecType.SIMPLE:
            SIMPLE_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamaSpecType.NESTED:
            NESTED_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamaSpecType.LAB_SPECIFIC:
            LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST.append(param_class)
        return param_class
    return decorator

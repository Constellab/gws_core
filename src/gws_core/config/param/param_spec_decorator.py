from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gws_core.config.param.param_spec import ParamSpec

# List all the param spec types annotated with the param_decorator
PARAM_SPEC_TYPES_LIST: list[type[ParamSpec]] = []

SIMPLE_PARAM_SPEC_TYPES_LIST: list[type[ParamSpec]] = []

NESTED_PARAM_SPEC_TYPES_LIST: list[type[ParamSpec]] = []

LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST: list[type[ParamSpec]] = []


class ParamSpecType(Enum):
    SIMPLE = "simple"
    NESTED = "nested"
    LAB_SPECIFIC = "lab_specific"


def param_spec_decorator(type_: ParamSpecType = ParamSpecType.SIMPLE) -> Callable:
    """Decorator of ParamSpec class to add it to the list of param spec types"""

    def decorator(param_class: type[ParamSpec]):
        from gws_core.config.param.param_spec import ParamSpec

        if not issubclass(param_class, ParamSpec):
            raise Exception("The param decorator can only be used on a ParamSpec child class")
        PARAM_SPEC_TYPES_LIST.append(param_class)
        if type_ == ParamSpecType.SIMPLE:
            SIMPLE_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamSpecType.NESTED:
            NESTED_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamSpecType.LAB_SPECIFIC:
            LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST.append(param_class)
        return param_class

    return decorator

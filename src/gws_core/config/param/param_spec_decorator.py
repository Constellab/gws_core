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

COMPUTED_PARAM_SPEC_TYPES_LIST: list[type[ParamSpec]] = []


class ParamSpecCategory(Enum):
    SIMPLE = "simple"
    NESTED = "nested"
    LAB_SPECIFIC = "lab_specific"
    COMPUTED = "computed"


def param_spec_decorator(
    label: str, type_: ParamSpecCategory = ParamSpecCategory.SIMPLE
) -> Callable:
    """Decorator of ParamSpec class to add it to the list of param spec types.

    :param label: Human-readable label of the param spec, shown in the UI when
        choosing a param type (e.g. "Short text" for StrParam).
    :param type_: Category of the param spec.
    """

    def decorator(param_class: type[ParamSpec]):
        from gws_core.config.param.param_spec import ParamSpec

        if not issubclass(param_class, ParamSpec):
            raise Exception("The param decorator can only be used on a ParamSpec child class")
        param_class.__category__ = type_
        param_class.__label__ = label
        PARAM_SPEC_TYPES_LIST.append(param_class)
        if type_ == ParamSpecCategory.SIMPLE:
            SIMPLE_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamSpecCategory.NESTED:
            NESTED_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamSpecCategory.LAB_SPECIFIC:
            LAB_SPECIFIC_PARAM_SPEC_TYPES_LIST.append(param_class)
        elif type_ == ParamSpecCategory.COMPUTED:
            COMPUTED_PARAM_SPEC_TYPES_LIST.append(param_class)
        return param_class

    return decorator

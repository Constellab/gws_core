from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gws_core.config.param.param_spec import ParamSpec


class ParamSpecCategory(Enum):
    SIMPLE = "simple"
    NESTED = "nested"
    LAB_SPECIFIC = "lab_specific"
    COMPUTED = "computed"


# Param spec types annotated with @param_spec_decorator, indexed by category.
PARAM_SPEC_TYPES_BY_CATEGORY: dict[ParamSpecCategory, list[type[ParamSpec]]] = {
    category: [] for category in ParamSpecCategory
}


def param_spec_decorator(
    type_: ParamSpecCategory = ParamSpecCategory.SIMPLE,
) -> Callable:
    """Decorator of ParamSpec class to add it to the list of param spec types.

    :param type_: Category of the param spec.
    """

    def decorator(param_class: type[ParamSpec]):
        from gws_core.config.param.param_spec import ParamSpec

        if not issubclass(param_class, ParamSpec):
            raise Exception("The param decorator can only be used on a ParamSpec child class")
        param_class.__category__ = type_
        PARAM_SPEC_TYPES_BY_CATEGORY[type_].append(param_class)
        return param_class

    return decorator

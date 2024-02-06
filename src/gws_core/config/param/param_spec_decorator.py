# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, List, Type

if TYPE_CHECKING:
    from gws_core.config.param.param_spec import ParamSpec

# from gws_core.config.param.param_spec_helper import ParamSpecHelper

# List all the param spec types annotated with the param_decorator
PARAM_SPEC_TYPES_LIST: List[Type[ParamSpec]] = []


def param_spec_decorator():
    """Decorator of ParamSpec class to add it to the list of param spec types
    """
    def decorator(param_class: Type[ParamSpec]):
        from gws_core.config.param.param_spec import ParamSpec

        if not issubclass(param_class, ParamSpec):
            raise Exception("The param decorator can only be used on a ParamSpec child class")
        PARAM_SPEC_TYPES_LIST.append(param_class)
        return param_class
    return decorator

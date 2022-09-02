# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from gws_core.config.param_spec import ParamSpec

if TYPE_CHECKING:
    from gws_core.resource.resource import Resource


class LazyViewParam():
    """Param for resource view. With this param you can define a method in your resource and reference it in func_name
    This function must return a ParamSpec and this is useful to configure spec dynamically.
    """

    func_name: str
    default_param_spec: ParamSpec

    def __init__(self, func_name: str, default_param_spec: ParamSpec):
        """

        :param func_name: name of the resource function to call when retrieving the specs
        :type func_name: str
        """
        self.func_name = func_name

        if not isinstance(default_param_spec, ParamSpec):
            raise Exception('The default_param_spec of the LazyViewParam is not a ParamSpec')
        self.default_param_spec = default_param_spec

    def generate_param_spec(self, resource: Resource) -> ParamSpec:
        func: Callable = getattr(resource, self.func_name)
        param_spec = func()

        if not isinstance(param_spec, ParamSpec):
            raise Exception('The LazyViewParam did not returned a ParamSpec')

        return param_spec

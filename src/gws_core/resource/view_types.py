from typing import Any, Dict, TypedDict

from ..config.param_spec import ParamSpec

ViewSpecs = Dict[str, ParamSpec]


class ViewConfig(TypedDict):
    """Object used when calling a vue to passe parameters to the method and then to the view

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    view_config: Dict[str, Any]
    method_config: Dict[str, Any]

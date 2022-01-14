# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, TypedDict, Union

from ..config.param_spec import ParamSpec
from .lazy_view_param import LazyViewParam

ViewSpecs = Dict[str, Union[ParamSpec, LazyViewParam]]


class ViewCallResult(TypedDict):
    """Object used to return the call of a view

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    view_human_name: str
    view_short_description: str
    view_data: Any

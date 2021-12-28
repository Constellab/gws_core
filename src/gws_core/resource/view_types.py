# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Union

from ..config.param_spec import ParamSpec
from .lazy_view_param import LazyViewParam

ViewSpecs = Dict[str, Union[ParamSpec, LazyViewParam]]

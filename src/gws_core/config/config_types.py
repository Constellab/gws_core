# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from .param.param_spec import ParamSpec
from .param.param_types import ParamValue

ConfigParamsDict = Dict[str, ParamValue]
ConfigSpecs = Dict[str, ParamSpec]

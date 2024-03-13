

from typing import Dict

from .param.param_spec import ParamSpec
from .param.param_types import ParamValue

ConfigParamsDict = Dict[str, ParamValue]
ConfigSpecs = Dict[str, ParamSpec]

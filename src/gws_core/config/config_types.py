# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from typing_extensions import TypedDict

from .param.param_spec import ParamSpec
from .param.param_types import ParamSpecDict, ParamValue

ConfigParamsDict = Dict[str, ParamValue]
ConfigSpecs = Dict[str, ParamSpec]


class ConfigDict(TypedDict):
    """Config values send to the task
    """

    # specification of the config
    specs: Dict[str, ParamSpecDict]

    # values of the config
    values: ConfigParamsDict

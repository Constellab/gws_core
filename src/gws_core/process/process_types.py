# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from typing_extensions import TypedDict

from gws_core.config.param.param_types import ParamSpecDict
from gws_core.io.io_spec import IOSpecDict
from gws_core.model.typing_dict import TypingDict


class ProcessSpecDict(TypingDict):
    input_specs: Dict[str, IOSpecDict]
    output_specs: Dict[str, IOSpecDict]
    config_specs: Dict[str, ParamSpecDict]


class ProcessErrorInfo(TypedDict):
    detail: str
    unique_code: str
    context: str
    instance_id: str

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Optional

from typing_extensions import TypedDict

from gws_core.config.config_types import ConfigDict
from gws_core.config.param.param_types import ParamSpecDict
from gws_core.io.io import IODict
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


class ProcessMinimumDict(TypedDict):
    id: str
    process_typing_name: str


class ProcessConfigDict(TypedDict):
    process_typing_name: str
    instance_name: str
    config: ConfigDict
    human_name: str
    short_description: str
    brick_version: str
    inputs: IODict
    outputs: IODict
    status: str
    # for sub protocol, recursive graph
    graph: Optional[dict]

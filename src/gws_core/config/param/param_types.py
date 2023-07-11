# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Literal, Optional, Type

from typing_extensions import TypedDict

ParamValue = Any
ParamValueType = Type[ParamValue]


# Visibility of a param
# Public --> main param visible in the first config section in the interface
# Protected --> considered as advanced param, it will be in the advanced section in the interface (it must have a default value or be optional)
# Private --> private param, it will not be visible in the interface (it must have a default value or be optional)
ParamSpecVisibilty = Literal["public", "protected", "private"]


class ParamSpecDict(TypedDict):
    type: str
    optional: bool
    default_value: Optional[ParamValue]
    unit: Optional[str]
    human_name: Optional[str]
    short_description: Optional[str]
    visibility: Optional[ParamSpecVisibilty]
    allowed_values: Optional[List[ParamValue]]
    additional_info: Dict[str, str]

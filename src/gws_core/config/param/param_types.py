# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Literal, Optional, Type, TypedDict, Union

ParamValue = Union[str, int, float, bool, list, dict]
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

    # Numeric
    min_value: Optional[float]
    max_value: Optional[float]

    # Params set
    max_number_of_occurrences: Optional[int]
    param_set: Optional[Dict[str, 'ParamSpecDict']]

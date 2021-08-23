from __future__ import annotations  # for Python 3.7-3.9

from typing import Any, Dict, List, Optional, Type, TypedDict, Union

ConfigSpecType = Union[Type[str], Type[int], Type[float], Type[bool], Type[list], Type[dict]]

ConfigParamType = Union[str, int, float, bool, list, dict]

# TODO replace Optional with NotRequired when NotRequired works


class ConfigSpec(TypedDict, total=False):

    # Type of the config value (string, float...)
    type: ConfigSpecType

    #  Default value
    #  If not provided, the config is mandatory
    default: Optional[Any]

    #  If present, the value must be in the array
    allowed_values: Optional[List[Any]]

    # Description of the config, showed in the interface
    description: Optional[str]

   # Measure unit of the value (ex km)
    unit: Optional[str]


ConfigSpecs = Dict[str, ConfigSpec]

from __future__ import annotations  # for Python 3.7-3.9

from typing import Any, Dict, List, Optional, Type, TypedDict, Union

from gws_core.core.classes.validator import Validator
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

ConfigSpecType = Union[Type[str], Type[int], Type[float], Type[bool], Type[list], Type[dict]]

ConfigValue = Union[str, int, float, bool, list, dict]
ConfigValues = Dict[str, ConfigValue]


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


class ConfigSpecsHelper():

    @staticmethod
    def check_config(name: str, value: ConfigValue, specs: ConfigSpecs) -> ConfigValue:
        """Method that check a config value is compatible with the corresponding specs in the configs
        """
        if not name in specs:
            raise BadRequestException(f"Config with name '{name}' does not exist.")

        try:
            validator = Validator.from_specs(**specs[name])
            return validator.validate(value)
        except Exception as err:
            raise BadRequestException(
                f"Invalid parameter value '{name}'. Error message: {err}") from err

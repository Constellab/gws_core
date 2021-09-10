from __future__ import annotations  # for Python 3.7-3.9

from typing import Any, Dict, List, Optional, Type, TypedDict, Union

from ..core.classes.validator import Validator
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException

ConfigValue = Union[str, int, float, bool, list, dict]
ConfigSpecType = Type[ConfigValue]
ConfigValues = Dict[str, ConfigValue]


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

    # ONLY FOR NUMERIC. The minimum value allowed
    min: Optional[float]

    # ONLY FOR NUMERIC. The maximum value allowed
    max: Optional[float]


ConfigSpecs = Dict[str, ConfigSpec]


class ConfigSpecsHelper():

    @classmethod
    def check_config(cls, name: str, value: ConfigValue, specs: ConfigSpecs) -> ConfigValue:
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

    @classmethod
    def config_specs_to_json(cls, config_specs: ConfigSpecs) -> Dict[str, Any]:
        _json: Dict[str, Any] = {}
        for key, spec in config_specs.items():
            _json[key] = spec

            # if the type is a real type, get the name of it
            if "type" in spec and isinstance(spec["type"], type):
                _json[key]["type"] = spec["type"].__name__
        return _json

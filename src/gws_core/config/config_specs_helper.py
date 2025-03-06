

from typing import Any, Dict

from gws_core.config.param.param_types import ParamSpecDTO

from ..core.exception.exceptions import BadRequestException
from .config_types import ConfigSpecs
from .param.param_spec_helper import ParamSpecHelper


class ConfigSpecsHelper():

    @classmethod
    def check_config_specs(cls, specs: ConfigSpecs) -> None:
        """Check if the config spec is valid
        """

        if not isinstance(specs, dict):
            raise BadRequestException("The specs must be a dictionnary")

    @classmethod
    def config_specs_to_dto(cls, specs: ConfigSpecs, skip_private: bool = True) -> Dict[str, ParamSpecDTO]:
        """convert the config specs to json
        """
        json_: Dict[str, Any] = {}
        for key, spec in specs.items():
            # skip private params
            if skip_private and spec.visibility == "private":
                continue
            json_[key] = spec.to_dto()

        return json_

    @classmethod
    def config_specs_from_json(cls, dict_: Dict[str, Any]) -> ConfigSpecs:
        """Create a config specs from a json
        """
        config_specs: ConfigSpecs = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_json(value)
        return config_specs

    @classmethod
    def config_specs_from_dto(cls, dict_: Dict[str, ParamSpecDTO]) -> ConfigSpecs:
        """Create a config specs from a dto
        """
        config_specs: ConfigSpecs = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_dto(value)
        return config_specs

    @classmethod
    def all_config_are_optional(cls, specs: ConfigSpecs) -> bool:
        """Check if all the config are optional
        """
        for spec in specs.values():
            if not spec.optional:
                return False

        return True

    @classmethod
    def has_visible_config_specs(cls, specs: ConfigSpecs) -> bool:
        """Check if the config has visible specs
        """
        for spec in specs.values():
            if spec.visibility != "private":
                return True

        return False

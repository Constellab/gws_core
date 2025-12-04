from typing import Any, Dict, List

from gws_core.config.config_exceptions import MissingConfigsException, UnkownParamException
from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.param.param_spec_helper import ParamSpecHelper

from .param.param_spec import ParamSpec
from .param.param_types import ParamSpecDTO


class ConfigSpecs:
    specs: Dict[str, ParamSpec] = None

    def __init__(self, specs: Dict[str, ParamSpec] = None) -> None:
        """Define the spec of a task or a view
        Example:
        ConfigSpecs({
            "param1": IntParam(human_name="Param 1", default_value=1),
            "param2": StrParam(human_name="Param 2", default_value="Hello")
        })

        :param specs: _description_, defaults to None
        :type specs: Dict[str, ParamSpec], optional
        """
        if specs is None:
            specs = {}

        self.specs = specs

    def has_spec(self, spec_name: str) -> bool:
        return spec_name in self.specs

    def has_specs(self) -> bool:
        return len(self.specs) > 0

    def check_spec_exists(self, spec_name: str) -> None:
        if not self.has_spec(spec_name):
            raise UnkownParamException(spec_name)

    def get_spec(self, spec_name: str) -> ParamSpec:
        self.check_spec_exists(spec_name)
        return self.specs[spec_name]

    def update_spec(self, spec_name: str, spec: ParamSpec) -> None:
        self.check_spec_exists(spec_name)
        self.specs[spec_name] = spec

    def add_spec(self, spec_name: str, spec: ParamSpec) -> None:
        if spec_name in self.specs:
            raise Exception(f"The spec {spec_name} already exists")
        self.specs[spec_name] = spec

    def add_or_update_spec(self, spec_name: str, spec: ParamSpec) -> None:
        self.specs[spec_name] = spec

    def remove_spec(self, spec_name: str) -> None:
        self.check_spec_exists(spec_name)
        del self.specs[spec_name]

    def merge_specs(self, specs2: "ConfigSpecs") -> "ConfigSpecs":
        """Merge two ConfigSpecs objects"""
        for key, spec in specs2.specs.items():
            self.add_or_update_spec(key, spec)
        return self

    def to_dto(self, skip_private: bool = True) -> Dict[str, ParamSpecDTO]:
        """convert the config specs to json"""
        json_: Dict[str, Any] = {}
        for key, spec in self.specs.items():
            # skip private params
            if skip_private and spec.visibility == "private":
                continue
            json_[key] = spec.to_dto()

        return json_

    def to_json_dict(self, skip_private: bool = True) -> Dict[str, Any]:
        """convert the config specs to json"""
        dto = self.to_dto(skip_private)
        return {key: value.to_json_dict() for key, value in dto.items()}

    def all_config_are_optional(self) -> bool:
        """Check if all the config are optional"""
        for spec in self.specs.values():
            if not spec.optional:
                return False

        return True

    def has_visible_config_specs(self) -> bool:
        """Check if the config has visible specs"""
        for spec in self.specs.values():
            if spec.visibility != "private":
                return True

        return False

    def mandatory_values_are_set(self, param_values: ConfigParamsDict) -> bool:
        """
        check that all mandatory configs are provided
        """
        if self.specs is None:
            return True

        for key, spec in self.specs.items():
            if not spec.optional and param_values.get(key, None) is None:
                return False

        return True

    def check_config_specs(self) -> None:
        """Check that the config specs are valid"""
        if not self.specs:
            return

        if not isinstance(self.specs, dict):
            raise Exception("The config specs must be a dictionary")

        for key, item in self.specs.items():
            if not isinstance(item, ParamSpec):
                raise Exception(
                    f"The config spec '{key}' is invalid, it must be a ParamSpec but got {type(item)}"
                )

    def build_config_params(self, param_values: ConfigParamsDict) -> ConfigParams:
        """
        Build the ConfigParams from the param_specs and param_values.
        ConfigParam is supposed to be used directly not stored.
        Check the param_values with params_specs and return ConfigParams if ok.
        ConfigParams contains all value and default value if not provided

        :param param_specs: [description]
        :type param_specs: ConfigSpecs
        :param param_values: [description]
        :type param_values: ConfigParamsDict
        :return: [description]
        :rtype: ConfigParams
        """
        values = self.get_and_check_values(param_values)

        # apply transform function of specs if needed
        for key, spec in self.specs.items():
            values[key] = spec.build(values[key])

        return ConfigParams(values)

    def get_and_check_values(self, param_values: ConfigParamsDict) -> ConfigParamsDict:
        """
        Check and validate all values based on spec
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        if param_values is None:
            param_values = {}

        full_values: ConfigParamsDict = {}
        missing_params: List[str] = []

        for key, spec in self.specs.items():
            # if the config was not set
            if not key in param_values or param_values[key] is None:
                if spec.optional:
                    full_values[key] = spec.get_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(spec.human_name or key)
            else:
                full_values[key] = spec.validate(param_values[key])

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return full_values

    def get_default_values(self) -> ConfigParamsDict:
        default_values = {}
        for key, spec in self.specs.items():
            default_values[key] = spec.get_default_value()
        return default_values

    def __len__(self) -> int:
        return len(self.specs)

    @classmethod
    def from_json(cls, dict_: Dict[str, Any]) -> "ConfigSpecs":
        """Create a config specs from a json"""
        config_specs: Dict[str, ParamSpec] = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_json(value)
        return cls(config_specs)

    @classmethod
    def from_dto(cls, dict_: Dict[str, ParamSpecDTO]) -> "ConfigSpecs":
        """Create a config specs from a dto"""
        config_specs: Dict[str, ParamSpec] = {}
        for key, value in dict_.items():
            config_specs[key] = ParamSpecHelper.create_param_spec_from_dto(value)
        return cls(config_specs)

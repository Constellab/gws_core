from typing import Dict, List

from gws_core.config.config_exceptions import MissingConfigsException
from gws_core.config.config_types import ConfigParams, ConfigSpecs, ParamValue
from gws_core.config.param_spec import ParamSpec


class ParamSpecHelper():

    @classmethod
    def get_and_check_values(
            cls, param_specs: Dict[str, ParamSpec],
            param_values: Dict[str, ParamValue]) -> Dict[str, ParamValue]:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        if param_specs is None:
            param_specs = {}
        if param_values is None:
            param_values = {}

        full_values: Dict[str, ParamValue] = {}
        missing_params: List[str] = []

        for key, spec in param_specs.items():
            # if the config was not set
            if not key in param_values:
                if spec.optional:
                    full_values[key] = spec.get_default_value()
                else:
                    # if there is not default value the value is missing
                    missing_params.append(key)
            else:
                full_values[key] = param_values[key]

        # If there is at least one missing param, raise an exception
        if len(missing_params) > 0:
            raise MissingConfigsException(missing_params)

        return full_values

    @classmethod
    def get_config_params(cls, param_specs: Dict[str, ParamSpec],
                          param_values: Dict[str, ParamValue]) -> ConfigParams:
        """ Check the param_values with params_specs and return ConfigParams if ok. ConfigParams contains all value and default value if not provided

        :param param_specs: [description]
        :type param_specs: Dict[str, ParamSpec]
        :param param_values: [description]
        :type param_values: Dict[str, ParamValue]
        :return: [description]
        :rtype: ConfigParams
        """
        return ConfigParams(ParamSpecHelper.get_and_check_values(param_specs, param_values))

    @classmethod
    def check_config_specs(cls, config_specs: ConfigSpecs) -> None:
        """Check that the config specs are valid
        """
        if not config_specs:
            return

        if not isinstance(config_specs, dict):
            raise Exception("The config specs must be a dictionary")

        for key, item in config_specs.items():
            if not isinstance(item, ParamSpec):
                raise Exception(f"The config spec '{key}' is invalid, it must be a ParamSpec but got {type(item)}")

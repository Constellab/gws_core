

from typing import Any, Dict, final

from gws_core.config.config_dto import ConfigDTO, ConfigSimpleDTO
from gws_core.core.model.db_field import JSONField

from ..core.model.model_with_user import ModelWithUser
from .config_exceptions import InvalidParamValueException
from .config_params import ConfigParamsDict
from .config_specs import ConfigSpecs
from .param.param_spec import ParamSpec
from .param.param_types import ParamSpecDTO, ParamValue


@final
class Config(ModelWithUser):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """

    data: Dict[str, Any] = JSONField(null=True)

    _table_name = 'gws_config'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved():
            self.data = {
                "specs": {},
                "values": {}
            }

    ########################################## SPEC #####################################

    def get_specs(self) -> ConfigSpecs:
        return ConfigSpecs.from_json(self.data["specs"])

    def set_specs(self, specs: ConfigSpecs) -> None:
        specs.check_config_specs()
        self.data["specs"] = specs.to_json_dict(skip_private=False)

    def update_spec(self, name, spec: ParamSpec) -> None:
        specs = self.get_specs()
        specs.update_spec(name, spec)
        self.set_specs(specs)

    def has_spec(self, param_name: str) -> bool:
        return self.get_specs().has_spec(param_name)

    def get_spec(self, param_name: str) -> ParamSpec:
        return self.get_specs().get_spec(param_name)

    ########################################## PARAM  #####################################

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data.get("specs", {})

    ########################################## VALUE #####################################

    def get_values(self) -> ConfigParamsDict:
        return self.data["values"]

    def get_value(self, param_name: str) -> Any:
        """
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """
        default = self.get_spec(param_name).get_default_value()
        return self.data.get("values", {}).get(param_name, default)

    def get_and_check_values(self) -> ConfigParamsDict:
        """
        Returns all the parameters including default value if not provided

        raises MissingConfigsException: If one or more mandatory params where not provided it raises a MissingConfigsException

        :return: The parameters
        :rtype: `dict`
        """

        values: ConfigParamsDict = self.get_values()
        specs: ConfigSpecs = self.get_specs()

        return specs.get_and_check_values(values)

    def set_value(self, param_name: str, value: ParamValue, skip_validate: bool = False):
        """
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """
        if not skip_validate:
            try:
                value = self.get_spec(param_name).validate(value)
            except Exception as err:
                raise InvalidParamValueException(param_name, value, str(err))

        if "values" not in self.data:
            self.data["values"] = {}

        self.data["values"][param_name] = value

    def set_values(self, values: ConfigParamsDict):
        """
        Set config parameters
        """
        self._clear_values()

        for k in values:
            self.set_value(k, values[k])

    def value_is_set(self, name: str) -> bool:
        """
        Test if a parameter exists and is not none

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data["values"] and self.data["values"][name] is not None

    def mandatory_values_are_set(self) -> bool:
        return self.get_specs().mandatory_values_are_set(self.get_values())

    def _clear_values(self):
        self.data["values"] = {}

    def to_dto(self) -> ConfigDTO:

        specs = self.to_specs_dto()

        # get the values of the config (skip private values)
        values = {}
        for key, spec in specs.items():
            if spec.visibility == "private":
                continue
            values[key] = self.get_value(key)

        return ConfigDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            specs=specs,
            values=values
        )

    def to_simple_dto(self, ignore_values: bool = False) -> ConfigSimpleDTO:
        """
        Export the config to a dict
        """

        return ConfigSimpleDTO(
            specs=self.to_specs_dto(skip_private=False),
            values=self.get_values() if not ignore_values else {}
        )

    @classmethod
    def from_simple_dto(cls, config_dto: ConfigSimpleDTO) -> 'Config':
        """
        Import the config from a dto
        """

        config = Config()
        config.set_specs(ConfigSpecs.from_dto(config_dto.specs))
        config.set_values(config_dto.values)

        return config

    def copy(self) -> 'Config':
        """Copy the config to a new Config with a new Id
        """

        new_config: Config = Config()
        new_config.data = self.data
        return new_config

    def to_specs_dto(self, skip_private: bool = True) -> Dict[str, ParamSpecDTO]:
        return self.get_specs().to_dto(skip_private=skip_private)

    class Meta:
        table_name = 'gws_config'

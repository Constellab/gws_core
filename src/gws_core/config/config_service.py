

from .config import Config
from .config_types import ConfigParamsDict
from .param.param_types import ParamValue


class ConfigService():

    @classmethod
    def update_config_params_with_id(cls, id: str, config_params: ConfigParamsDict) -> Config:
        config: Config = Config.get_by_id_and_check(id)

        return cls.update_config_params(config, config_params)

    @classmethod
    def update_config_params(cls, config: Config, config_params: ConfigParamsDict) -> Config:
        config.set_values(config_params)

        return config.save()

    @classmethod
    def update_config_value(cls, config: Config, param_name: str, value: ParamValue) -> Config:
        config.set_value(param_name, value)

        return config.save()

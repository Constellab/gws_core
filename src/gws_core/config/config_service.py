# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParamsDict, ParamValue

from ..core.service.base_service import BaseService
from .config import Config


class ConfigService(BaseService):

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

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union, Type
from ..config.config_types import ConfigParams, ConfigParamsDict, ParamValue
from ..config.config import Config
from ..resource.view import View

class ViewTester():
    """ ViewTester """
    _view: View
    
    def __init__(self, view: View):
        self._view = view

    def to_dict(self, params: ConfigParamsDict = None):
        if params is None:
            params = {}

        params = self._get_and_check_config(params)
        return self._view.to_dict(params)

    def _get_and_check_config(self, params: ConfigParamsDict) -> ConfigParams:
        """Check and convert the config to ConfigParams

        :return: [description]
        :rtype: ConfigParams
        """
        config: Config = Config()
        config.set_specs(self._view._specs)
        config.set_values(params)
        return config.get_and_check_values()
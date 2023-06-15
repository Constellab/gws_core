# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from ..config.config_types import ConfigParams, ConfigParamsDict
from ..resource.view.view import View


class ViewTester():
    """ ViewTester """
    _view: View

    def __init__(self, view: View):
        self._view = view

    def to_dict(self, params: ConfigParamsDict = None) -> dict:
        if params is None:
            params = {}

        config_params: ConfigParams = self._build_config_params(params)
        return self._view.to_dict(config_params)

    def _build_config_params(self, params: ConfigParamsDict) -> ConfigParams:
        """Check and convert the config to ConfigParams

        :return: [description]
        :rtype: ConfigParams
        """
        return ParamSpecHelper.build_config_params(self._view._specs, params)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.resource.view.view_dto import ViewDTO

from ..config.config_params import ConfigParams
from ..config.config_types import ConfigParamsDict
from ..resource.view.view import View


class ViewTester():
    """ ViewTester """
    _view: View

    def __init__(self, view: View):
        self._view = view

    def to_dto(self, params: ConfigParamsDict = None) -> ViewDTO:
        if params is None:
            params = {}

        config_params: ConfigParams = self._build_config_params(params)
        return self._view.to_dto(config_params)

    def _build_config_params(self, params: ConfigParamsDict) -> ConfigParams:
        """Check and convert the config to ConfigParams

        :return: [description]
        :rtype: ConfigParams
        """
        return ParamSpecHelper.build_config_params(self._view._specs, params)

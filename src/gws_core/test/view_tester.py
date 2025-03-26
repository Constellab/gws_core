

from gws_core.config.config_params import ConfigParamsDict
from gws_core.resource.view.view_dto import ViewDTO

from ..config.config_params import ConfigParams
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
        return self._view._specs.build_config_params(params)

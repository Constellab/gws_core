# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable, Dict

from gws_core.config.config import Config
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigParamsDict
from gws_core.resource.resource import Resource

from ...config.config_params import ConfigParams
from ...config.param.param_spec_helper import ParamSpecHelper
from ..resource import Resource
from .view import View
from .view_helper import ViewHelper
from .view_meta_data import ResourceViewMetaData


class ViewRunner():

    resource: Resource
    view_name: str

    config_params: ConfigParams

    _view_metadata: ResourceViewMetaData = None

    _view: View = None

    def __init__(self, resource: Resource, view_name: str, config: ConfigParamsDict):
        self.resource = resource
        self.view_name = view_name
        self._build_config(config)

    def generate_view(self) -> View:
        view_metadata: ResourceViewMetaData = self._get_and_check_view_meta()

        # Get view method
        view_method: Callable = getattr(self.resource, view_metadata.method_name)

        # Get the view object from the view method
        view: View = view_method(self.config_params)

        if view is None or not isinstance(view, View):
            raise Exception(f"The view method '{view_metadata.method_name}' didn't returned a View object")

        # set view name if not defined
        if view.get_title() is None:
            view.set_title(self.resource.name + " - " + view_metadata.human_name)

        # set the resource technical infos
        if self.resource.technical_info:
            for value in self.resource.technical_info.get_all().values():
                view.add_technical_info(value)

        self._view = view
        return view

    def call_view_to_dict(self) -> Dict:
        if self._view is None:
            raise Exception("You must call generate_view_on_resource before call_view_to_dict")

        # create a new config for the view to_dict method based on view specs
        config_params: ConfigParams = ParamSpecHelper.build_config_params(self._view._specs, dict(self.config_params))

        return self._view.to_dict(config_params)

    def _get_and_check_view_meta(self) -> ResourceViewMetaData:
        if self._view_metadata is None:
            self._view_metadata = ViewHelper.get_and_check_view_meta(type(self.resource), self.view_name)

        return self._view_metadata

    def _build_config(self, config_values: ConfigParamsDict) -> None:
        metadata = self._get_and_check_view_meta()

        self.config_params = ParamSpecHelper.build_config_params(
            metadata.get_view_specs_from_resource(self.resource, skip_private=False), config_values)

    def get_config(self) -> Config:
        config = Config()
        config.set_specs(self._get_and_check_view_meta().get_view_specs_from_type(skip_private=False))
        config.set_values(self.config_params)

        return config
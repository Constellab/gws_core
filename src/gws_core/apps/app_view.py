
from __future__ import annotations

from gws_core.apps.app_dto import AppInstanceUrl
from gws_core.config.config_params import ConfigParams
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class AppView(View):
    """
    View an App instance.
    It return the app url which is used in an iframe to display the app.
    """
    _type: ViewType = ViewType.APP

    app_url: AppInstanceUrl = None

    def __init__(self, app_url: AppInstanceUrl = None):
        super().__init__()
        self.app_url = app_url

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "url": self.app_url
        }

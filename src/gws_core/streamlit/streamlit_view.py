# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from gws_core.config.config_params import ConfigParams
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class StreamlitView(View):
    """
    Use this view to return a section of a Table and enable pagination to retrieve other section.
    This view embed config to enable pagination.

    ```
    """
    _type: ViewType = ViewType.STREAMLIT

    streamlit_app_url: str = None

    def __init__(self, streamlit_app_url: str = None):
        super().__init__()
        self.streamlit_app_url = streamlit_app_url

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "url": self.streamlit_app_url
        }

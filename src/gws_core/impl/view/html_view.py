# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class HTMLView(View):
    """
    Class html view.

    The view model is:
    ```
    {
        "type": "html-view"
        "data": {'html': str}
    }
    ```
    """
    _type: ViewType = ViewType.HTML
    _html: str

    def __init__(self, html: str = None):
        super().__init__()
        self._html = html

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return {'html': self._html}

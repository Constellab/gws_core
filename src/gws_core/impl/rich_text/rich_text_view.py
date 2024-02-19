# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class RichTextView(View):
    """
    Class rich text view. Useful to show report content.

    The view model is:
    ```
    {
        "type": "rich-text-view"
        "data": {'content': RichTextDTO}
    }
    ```
    """
    _type: ViewType = ViewType.RICH_TEXT
    _rich_text: RichText

    def __init__(self, rich_text: RichText):
        super().__init__()
        self._rich_text = rich_text

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return {'content': self._rich_text.get_content_as_json()}

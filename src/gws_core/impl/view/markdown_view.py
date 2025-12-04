from gws_core.config.config_params import ConfigParams
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class MarkdownView(View):
    """
    Class html view.

    The view model is:
    ```
    {
        "type": "markdown-view"
        "data": {'markdown': str}
    }
    ```
    """

    _type: ViewType = ViewType.MARKDOWN
    _markdown: str

    def __init__(self, markdown: str = None):
        super().__init__()
        self._markdown = markdown

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return {"markdown": self._markdown}

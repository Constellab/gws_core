

from gws_core.config.config_params import ConfigParams
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class RichTextView(View):
    """
    Class rich text view. Useful to show note content.

    The view model is:
    ```
    {
        "type": "rich-text-view"
        "data": {'content': RichTextDTO}
    }
    ```
    """
    _type: ViewType = ViewType.RICH_TEXT
    _title: str
    object_type: RichTextObjectType
    object_id: str

    _rich_text: RichText

    def __init__(self, title: str, rich_text: RichText,
                 object_type: RichTextObjectType,
                 object_id: str):
        super().__init__()
        self._title = title
        self._rich_text = rich_text
        self.object_type = object_type
        self.object_id = object_id

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return {
            'title': self._title,
            'content': self._rich_text.to_dto_json_dict(),
            'object_type': self.object_type,
            'object_id': self.object_id
        }

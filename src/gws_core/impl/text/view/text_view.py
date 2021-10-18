from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ....config.param_spec import IntParam
from ....core.classes.paginator import PageInfo
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....resource.view import View
from ....resource.view_types import ViewSpecs

if TYPE_CHECKING:
    from ..text import Text


class TextView(View):
    """
    Class text view.

    The view model is:
    ```
    {
        "type": "text-view"
        "data": str
    }
    ```
    """

    _type: str = "text-view"
    _specs: ViewSpecs = {
        **View._specs,
        "page": IntParam(default_value=1, min_value=1, human_name="Page number"),
        "page_size": IntParam(
            default_value=10000, max_value=50000, min_value=1000, human_name="Number of caracters to display per page")
    }
    _data: str
    MAX_NUMBER_OF_CHARS_PER_PAGE = 50000

    def check_and_set_data(self, data: Union[str, Text]):
        from ..text import Text
        if not isinstance(data, (str, Text,)):
            raise BadRequestException("The data must be a string or an intance of Text")
        if isinstance(data, Text):
            data = data.get_data()
        self._data = data

    def _slice(self, from_char_index: int = 0, to_char_index: int = 3000) -> str:
        length = len(self._data)
        from_char_index = min(max(from_char_index, 0), length)
        to_char_index = min(min(to_char_index, from_char_index + self.MAX_NUMBER_OF_CHARS_PER_PAGE), length)
        return self._data[from_char_index:to_char_index]

    def to_dict(self, *args, **kwargs) -> dict:
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 10000)

        total_number_of_chars = len(self._data)
        page_info: PageInfo = PageInfo(page, page_size, total_number_of_chars, self.MAX_NUMBER_OF_CHARS_PER_PAGE, 1)

        text = self._slice(from_char_index=page_info.from_index, to_char_index=page_info.to_index)
        return {
            **super().to_dict(**kwargs),
            "data": text,
            **page_info.to_json(),
        }

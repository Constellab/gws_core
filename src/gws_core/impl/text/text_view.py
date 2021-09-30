from typing import Union

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...resource.view import View


class TextView(View):
    """
    Class text view.

    The view model is:
    ```
    {
        "type": "text-view"
        "title": str
        "subtitle": str
        "data": str
    }
    ```
    """

    _data: str
    MAX_NUMBER_OF_CHARS_PER_PAGE = 3000

    def __init__(self, data: Union[str, 'Text']):
        from .text import Text
        if not isinstance(data, (str, Text,)):
            raise BadRequestException("The data must be a string or an intance of Text")
        if isinstance(data, Text):
            data = data.get_data()
        super().__init__(type="text-view", data=data)

    def _slice(self, from_char_index: int = 0, to_char_index: int = 3000) -> str:
        length = len(self._data)
        from_char_index = min(max(from_char_index, 0), length)
        to_char_index = min(min(to_char_index, from_char_index + self.MAX_NUMBER_OF_CHARS_PER_PAGE), length)
        return self._data[from_char_index:to_char_index]

    def to_dict(self, page: int = 1, number_of_chars_per_page: int = 3000, title: str = None, subtitle: str = None) -> dict:
        number_of_chars_per_page = min(self.MAX_NUMBER_OF_CHARS_PER_PAGE, number_of_chars_per_page)
        from_char_index = (page-1)*number_of_chars_per_page
        to_char_index = from_char_index + number_of_chars_per_page
        total_number_of_chars = len(self._data)
        total_number_of_pages = int(len(self._data) / number_of_chars_per_page)

        text = self._slice(from_char_index=from_char_index, to_char_index=to_char_index)
        return {
            "type": self._type,
            "title": title,
            "subtile": subtitle,
            "data": text,
            "page": page,
            "number_of_chars_per_page": number_of_chars_per_page,
            "total_number_of_pages": total_number_of_pages,
            "from_char_index": from_char_index,
            "to_char_index": to_char_index,
            "total_number_of_chars": total_number_of_chars
        }

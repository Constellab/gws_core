

from typing import Any

from gws_core.config.config_specs import ConfigSpecs

from ...config.config_params import ConfigParams
from ...config.param.param_spec import IntParam
from ...core.classes.paginator import PageInfo
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...resource.view.view import View
from ...resource.view.view_types import ViewType

MAX_NUMBER_OF_CHARS_PER_PAGE = 50000


class TextViewData():
    text: str
    is_first_page: bool
    is_last_page: bool
    # value to use when calling the next page and previous page
    next_page: Any
    previous_page: Any
    # name of the param to use to change the page
    page_param_name: str

    def __init__(self, text: str, is_first_page: bool, is_last_page: bool,
                 next_page: Any = None, previous_page: Any = None, page_param_name: str = "page"):
        self.text = text
        self.is_first_page = is_first_page
        self.is_last_page = is_last_page
        self.next_page = next_page
        self.previous_page = previous_page
        self.page_param_name = page_param_name

    def to_json(self) -> dict:
        return {
            "text": self.text,
            "is_first_page": self.is_first_page,
            "is_last_page": self.is_last_page,
            "next_page": self.next_page,
            "previous_page": self.previous_page,
            "page_param_name": self.page_param_name
        }


class TextView(View):
    """
    Class text view that include pagination config

    The view model is:
    ```
    {
        "type": "text-view"
        "data": TextViewData
    }
    ```
    """

    _type: ViewType = ViewType.TEXT
    _specs = ConfigSpecs({"page": IntParam(default_value=1, min_value=1, human_name="Page number"), "page_size": IntParam(
        default_value=10000, max_value=MAX_NUMBER_OF_CHARS_PER_PAGE, min_value=1000, human_name="Number of caracters to display per page")})

    _data: str

    PAGE_PARAM_NAME = "page"

    def __init__(self, data: str):
        super().__init__()
        if not isinstance(data, str):
            raise BadRequestException("The data must be a string")
        self._data = data

    def _slice(self, from_char_index: int = 0, to_char_index: int = MAX_NUMBER_OF_CHARS_PER_PAGE) -> str:
        length = len(self._data)
        from_char_index = min(max(from_char_index, 0), length)
        to_char_index = min(to_char_index, from_char_index + MAX_NUMBER_OF_CHARS_PER_PAGE, length)
        return self._data[from_char_index:to_char_index]

    def data_to_dict(self, params: ConfigParams) -> dict:
        page = params.get_value("page")
        page_size = params.get_value("page_size")
        total_number_of_chars = len(self._data)
        page_info: PageInfo = PageInfo(page, page_size, total_number_of_chars, MAX_NUMBER_OF_CHARS_PER_PAGE, 1)

        text = self._slice(from_char_index=page_info.from_index, to_char_index=page_info.to_index)

        return TextViewData(
            text=text,
            # if interaction is disabled, disable pagination
            is_first_page=page_info.is_first_page or self.is_pagination_disabled(),
            is_last_page=page_info.is_last_page or self.is_pagination_disabled(),
            next_page=page_info.next_page,
            previous_page=page_info.prev_page,
            page_param_name=self.PAGE_PARAM_NAME
        ).to_json()


class SimpleTextView(View):
    """
    Class text view that does not include pagination config

    The view model is:
    ```
    {
        "type": "text-view"
        "data": TextViewData
    }
    ```
    """

    _type: ViewType = ViewType.TEXT

    _data: TextViewData

    def __init__(self, data: TextViewData):
        super().__init__()
        if not isinstance(data, TextViewData):
            raise BadRequestException("The data must be an instance of TextViewData")
        self._data = data

    def data_to_dict(self, params: ConfigParams) -> dict:
        return self._data.to_json()

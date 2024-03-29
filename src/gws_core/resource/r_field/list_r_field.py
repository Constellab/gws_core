

from typing import Any, List

from gws_core.core.utils.json_helper import JSONHelper

from ...core.classes.validator import ListValidator
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .primitive_r_field import PrimitiveRField


class ListRField(PrimitiveRField):

    def __init__(self, default_value: List = None, include_in_dict_view: bool = False) -> None:
        """
        RField to save a json like list. The ListRField only supports element that are either primitives python object or dictionary or lists.
        It Stringifies all python object to json using str method and replace NaN, inf by None.
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to []
        :type default_value: List, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=ListValidator(), searchable=False,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)

    def get_default_value(self) -> Any:
        if self._default_value is None:
            return []

        try:
            return JSONHelper.convert_dict_to_json(self._default_value)
        except:
            raise BadRequestException(
                "Incorrect default value for LstRField. The default value must be a json like list")

    def serialize(self, r_field_value: Any) -> Any:
        return super().serialize(JSONHelper.convert_dict_to_json(r_field_value))

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from copy import deepcopy
from typing import Any, Dict

from gws_core.core.classes.validator import DictValidator

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .primitive_r_field import PrimitiveRField


class DictRField(PrimitiveRField):

    def __init__(self, default_value: Dict = None, include_in_dict_view: bool = False) -> None:
        """
        RField to save a json like dictionary. The DictRField only supports element that are either primitives python object or dictionary or lists.
        It does not support python classes.
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to {}
        :type default_value: Dict, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=DictValidator(must_be_deep_jsonable=False), searchable=False,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)

    def get_default_value(self) -> Any:
        if self._default_value is None:
            return {}
        try:
            return deepcopy(self._default_value)
        except:
            raise BadRequestException(
                "Incorrect default value for DictRField. The default value must supports deepcopy")

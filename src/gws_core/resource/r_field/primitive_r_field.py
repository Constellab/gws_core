# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import uuid
from typing import Any

from ...core.classes.validator import (BoolValidator, FloatValidator,
                                       IntValidator, StrValidator, Validator)
from .r_field import BaseRField


class PrimitiveRField(BaseRField):
    """ RFeeld for primitives values, use subclass and not this one directly

    :param BaseRField: [description]
    :type BaseRField: [type]
    :return: [description]
    :rtype: [type]
    """

    validator: Validator

    def __init__(self, validator: Validator,
                 searchable: bool = False,
                 default_value: Any = None,
                 include_in_dict_view: bool = True) -> None:
        """
        :param validator: validator used on serialization and deserialization to verify r_field_value type
                          It also checks the default value
        :type validator: Validator
        :param searchable: if true, the field value is saved in the DB and could be search on a request
                           Only small amount of data can be mark as searchable, defaults to False
        :type searchable: bool, optional
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: Union[Type, Callable[[], Any], int, float, str, bool], optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        # check that the default value is correct
        default_value = validator.validate(default_value)
        super().__init__(searchable=searchable, default_value=default_value, include_in_dict_view=include_in_dict_view)
        self.validator = validator

    def deserialize(self, r_field_value: Any) -> Any:
        validated_value = self.validator.validate(r_field_value)
        return super().deserialize(validated_value)

    def serialize(self, r_field_value: Any) -> Any:
        validated_value = super().serialize(r_field_value)

        return self.validator.validate(validated_value)


class IntRField(PrimitiveRField):

    def __init__(self, default_value: int = None, include_in_dict_view: bool = True) -> None:
        """
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: int, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to True
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=IntValidator(), searchable=True,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)


class FloatRField(PrimitiveRField):

    def __init__(self, default_value: float = None, include_in_dict_view: bool = True) -> None:
        """
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: float, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to True
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=FloatValidator(), searchable=True,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)


class BoolRField(PrimitiveRField):

    def __init__(self, default_value: bool = None, include_in_dict_view: bool = True) -> None:
        """
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: bool, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to True
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=BoolValidator(), searchable=True,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)


class StrRField(PrimitiveRField):

    def __init__(self, searchable: bool = False,
                 default_value: str = None, include_in_dict_view: bool = True) -> None:
        """
        :param searchable: if true, the field value is saved in the DB and could be search on a request
                           Only small amount of data can be mark as searchable, defaults to False
        :type searchable: bool, optional
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: str, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=StrValidator(), searchable=searchable,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)


class UUIDRField(StrRField):

    def __init__(self, searchable: bool = False, include_in_dict_view: bool = True) -> None:
        """
        :param searchable: if true, the field value is saved in the DB and could be search on a request
                           Only small amount of data can be mark as searchable, defaults to False
        :type searchable: bool, optional
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: str, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(searchable=searchable, include_in_dict_view=include_in_dict_view)

    def get_default_value(self) -> Any:
        return str(uuid.uuid4())

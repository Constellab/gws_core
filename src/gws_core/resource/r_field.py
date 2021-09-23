
from copy import deepcopy
from inspect import isclass, isfunction
from typing import Any, Callable, Dict, List, Type, Union
import uuid

from ..core.classes.validator import (BoolValidator, DictValidator,
                                      FloatValidator, IntValidator,
                                      ListValidator, StrValidator, Validator)
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException


class BaseRField():
    """BaseRField, these fields must be used in resource attribute.
    When a class attribute is instantiated with an RField, it will be automatically
    save for output resource of a task and automatically initiated for input resource of a task
    """

    searchable: bool
    include_in_dict_view: bool
    _default_value: Any

    def __init__(self, searchable: bool = False,
                 default_value: Union[Type, Callable[[], Any], int, float, str, bool] = None,
                 include_in_dict_view: bool = False) -> None:
        """
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
        self.searchable = searchable
        self._default_value = default_value
        self.include_in_dict_view = include_in_dict_view

    def deserialize(self, r_field_value: Any) -> Any:
        if r_field_value is None:
            return self.get_default_value()

        return r_field_value

    def serialize(self, r_field_value: Any) -> Any:
        if r_field_value is None:
            return self.get_default_value()

        return r_field_value

    def get_default_value(self) -> Any:
        if self._default_value is None:
            return None

        # If the default value is a type or is a function, call it to
        # generate the default value
        if isclass(self._default_value) or isfunction(self._default_value):
            return self._default_value()

        # Verify the type
        # Allowing object would be dangerous as all the resource RField would share the same object
        if not isinstance(self._default_value, (int, bool, str, float)):
            raise BadRequestException(
                f"Invalid default value '{str(self._default_value)}' for the Rfield. It only supports primitive value (int, float, bool, str), type or function.")

        return self._default_value


class RField(BaseRField):
    """RField, these fields must be used in resource attribute.
    When a class attribute is instantiated with an RField, it will be automatically
    save for output resource of a task and automatically initiated for input resource of a task

    This field support a deserializer and serializer function to implement custom logic for saving and instantiating a resource

    """

    _deserializer: Callable
    _serializer: Callable

    def __init__(self, searchable: bool = False,
                 deserializer: Callable[[Any], Any] = None,
                 serializer: Callable[[Any], Any] = None,
                 default_value: Union[Type, Callable[[], Any], int, float, str, bool] = None,
                 include_in_dict_view: bool = False) -> None:
        """[summary]

        :param searchable: if true, the field value is saved in the DB and could be search on a request
                           Only small amount of data can be mark as searchable, defaults to False
        :type searchable: bool, optional
        :param deserializer: optional function that will be called manually deserialize the RField value, defaults to None
                             It is also possible to extend the RField class and override the deserialization method
        :type deserializer: Callable[[Any], Any], optional
        :param serializer: optional function that will be called to manually serialize the RField value, defaults to None
                            It is also possible to extend the RField class and override the serialization method
        :type serializer: Callable[[Any], Any], optional
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to None
        :type default_value: Union[Type, Callable[[], Any], int, float, str, bool], optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(searchable=searchable, default_value=default_value, include_in_dict_view=include_in_dict_view)
        self._deserializer = deserializer
        self._serializer = serializer

    def deserialize(self, r_field_value: Any) -> Any:
        """Method to deserialize the r_field_value, can be overriden by a child class

        :param r_field_value: value of the r_field
        :type r_field_value: Any
        """
        if r_field_value is None:
            return self.get_default_value()

        if self._deserializer is None:
            return r_field_value

        return self._deserializer(r_field_value)

    def serialize(self, r_field_value: Any) -> Any:
        """Method to serialize the r_field_value, can be overriden by a child class

        :param r_field_value: value of the r_field
        :type r_field_value: Any
        """
        if r_field_value is None:
            return self.get_default_value()

        if self._serializer is None:
            return r_field_value

        return self._serializer(r_field_value)


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
        self._default_value = (lambda: str(uuid.uuid4()))


class ListRField(PrimitiveRField):

    def __init__(self, default_value: List = None, include_in_dict_view: bool = False) -> None:
        """
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
            return deepcopy(self._default_value)
        except:
            raise BadRequestException("Incorrect default value for LstRField. The default value must supports deepcopy")


class DictRField(PrimitiveRField):

    def __init__(self, default_value: Dict = None, include_in_dict_view: bool = False) -> None:
        """
        :param default_value: default value of the resource attribute
                              Support primitive value, Type of Callable function
                              If type or callable, it will be called without parameter to initialise the default value, defaults to {}
        :type default_value: Dict, optional
        :param include_in_dict_view: if true, this field we be included in the default dict view
                              Do not mark huge fields as include in dict view, defaults to False
        :type include_in_dict_view: bool, optional
        """
        super().__init__(validator=DictValidator(), searchable=False,
                         default_value=default_value, include_in_dict_view=include_in_dict_view)

    def get_default_value(self) -> Any:
        if self._default_value is None:
            return {}
        try:
            return deepcopy(self._default_value)
        except:
            raise BadRequestException(
                "Incorrect default value for DictRField. The default value must supports deepcopy")

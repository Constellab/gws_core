
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math
import re
from typing import Any, Literal, Union

from ..exception.exceptions import BadRequestException
from .path import URL, Path

ValidatorType = Literal['bool', 'int', 'float', 'str', 'list', 'dict']


class Validator:
    """
    Base validator class
    Base validator allows validating serialized (or deserialized) parameter values according to a
    `type`.

    Usage: This class should not be used as it, but rather use to implement validator subclasses.
    It provides the construction :meth:`from_specs` to create usable basic validators.

    For example:
        * ```Validator.from_specs(type=int, default_value=5) -> IntValidator(default_value=5)```
        * ```Validator.from_specs(type=bool, default_value=True) -> BoolValidator(default_value=True)```
        * ```Validator.from_specs(type=float, default_value=5.5) -> FloatValidator(default_value=5.5)```
        * ```Validator.from_specs(type=str, default_value='foo') -> StrValidator(default_value='foo')```
        * ```Validator.from_specs(type=list, default_value=[1,"foo"]) -> ListValidator(default_value=[1,"foo"])```
        * ```Validator.from_specs(type=dict, default_value={"foo":1}) -> DictValidator(default_value={"foo":1})```

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: any
    :property type: The expected type of the value
    :type type: type
    """

    _type = None
    _default = None
    _allowed_values: list = None

    _valid_types = ['bool', 'int', 'float', 'str', 'list', 'dict']

    def __init__(self, default_value: Any = None, type_: ValidatorType = None, allowed_values: list = None, **kwargs):
        if not type_ is None:
            self._type = type_

        if not allowed_values is None:
            if isinstance(allowed_values, list):
                self._allowed_values = allowed_values
            else:
                raise BadRequestException(
                    "The parameter allowed_values must be a list")

        if not default_value is None:
            try:
                self._default = self._validate(default_value)
            except Exception as err:
                raise BadRequestException(
                    f"The default_value value is not valid. Error message: {err}")

    @property
    def type(self) -> type:
        if self._type == bool or self._type == 'bool':
            return bool
        elif self._type == int or self._type == 'int':
            return int
        elif self._type == float or self._type == 'float':
            return float
        elif self._type == str or self._type == 'str':
            return str
        elif self._type == list or self._type == 'list':
            return list
        elif self._type == dict or self._type == 'dict':
            return dict
        else:
            raise BadRequestException("Invalid type")

    def validate(self, value: Union[bool, int, float, str, list, dict]) -> Any:
        """
        Valitates a value.

        Checks if the type of :param:value is a valid subtype of :property:type and that
        :param:value is serializable/deserilizable (using built-in Python methods :meth:`json.dumps`/:meth:`json.loads`).

        Usage:
            * ```Validator.from_specs(type=int, default_value=5) -> IntValidator(default_value=5)```
            * ```Validator.from_specs(type=bool, default_value=True) -> BoolValidator(default_value=True)```
            * ```Validator.from_specs(type=float, default_value=5.5) -> FloatValidator(default_value=5.5)```
            * ```Validator.from_specs(type=str, default_value='foo') -> StrValidator(default_value='foo')```
            * ```Validator.from_specs(type=list, default_value=[1,"foo"]) -> ListValidator(default_value=[1,"foo"])```
            * ```Validator.from_specs(type=dict, default_value={"foo":1}) -> DictValidator(default_value={"foo":1})```

        :param value: The value to validate
        :type value: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        :return: The validated value
        :rtype: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        """
        if value is None:
            value = self._default

        if value is None:
            return value

        value = self._validate(value)

        if (not self._allowed_values is None) and len(self._allowed_values):
            if value in self._allowed_values:
                return value
            else:
                raise BadRequestException(
                    f"Invalid value '{value}'. Allowed values are {self._allowed_values}")
        else:
            return value

    def _validate(self, value):
        if not isinstance(self.type, type):
            raise BadRequestException(
                f"The validator is not well configured. Invalid type {self.type}.")

        if type(value) == self.type:
            if isinstance(value, (list, dict,)):
                try:
                    is_serilizable = (json.loads(json.dumps(value)) == value)
                except:
                    is_serilizable = False

                if not is_serilizable:
                    raise BadRequestException(
                        f"The value {value} is not serializable.")

            return value
        else:
            is_maybe_convertible_without_floating_error = not isinstance(value, bool) and \
                isinstance(value, (int, float,)) and self.type in (int, float,)
            if is_maybe_convertible_without_floating_error:
                is_valid = (self.type(value) == value)
                if not is_valid:
                    raise BadRequestException(
                        f"The value {value} cannot be casted to the class {self.type} with floating point alteration.")

                return self.type(value)

        if isinstance(value, str):
            try:
                value = json.loads(value)
                is_maybe_convertible_without_floating_error = not isinstance(value, bool) and \
                    isinstance(value, (int, float,)
                               ) and self.type in (int, float,)
                if is_maybe_convertible_without_floating_error:
                    is_valid = math.isnan(value) or (self.type(value) == value)
                    if not is_valid:
                        raise BadRequestException(
                            f"The value {value} cannot be casted to the class {self.type} with floating point alteration.")

                    return self.type(value)
                elif type(value) != self.type:
                    raise BadRequestException(
                        f"The deserialized value must be an instance of {self.type}. The actual deserialized value is {value}.")

            except Exception as err:
                raise BadRequestException(
                    f"The value cannot be deserialized. Please give a valid serialized string value. Error message: {err}")

            return value
        else:
            raise BadRequestException(f"Invalid value {value}")


class BoolValidator(Validator):
    """
    Validator class.

    This validator allows validating serialized (or deserialized) boolean parameter values.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: bool

    Usage: Let `validator = BoolValidator(default_value=True)`, then
        * `validator.validate(False) -> False`
        * `validator.validate(True) -> True`
        * `validator.validate(None) -> True if defaults to True`
        * `validator.validate('true') -> True`
        * `validator.validate('false') -> False`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate(4) -> ValueError`
    """

    _type = bool

    def __init__(self, default_value=None, **kwargs):
        super().__init__(default_value=default_value, type_=bool, **kwargs)


class NumericValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) numerical parameter values.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: int
    :property min_value: The default_value value returned by method :meth:`validate`
    :type min_value: int
    :property max_value: The default_value value returned by method :meth:`validate`
    :type max_value: int

    Usage: Let `validator = IntValidator(default_value=5)`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate(None) -> 5`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """

    _min_value = None
    _max_value = None
    _include_min = True
    _include_max = True

    def __init__(self, default_value=None, type=float, min_value=-math.inf, max_value=math.inf, include_min=False,
                 include_max=False, allowed_values=None, **kwargs):

        if min_value is None:
            self._min_value = -math.inf
        else:
            self._min_value = min_value

        if max_value is None:
            self._max_value = math.inf
        else:
            self._max_value = max_value

        self._include_min = include_min
        self._include_max = include_max
        if math.isfinite(self._min_value):
            self._include_min = True

        if math.isfinite(self._max_value):
            self._include_max = True

        super().__init__(default_value=default_value, type_=type,
                         allowed_values=allowed_values, **kwargs)

    def _validate(self, value):
        value = super()._validate(value)
        if value < self._min_value or (value == self._min_value and not self._include_min):
            raise BadRequestException(
                f"The value must be greater than {self._min_value}. The actual value is {value}")

        if value > self._max_value or (value == self._max_value and not self._include_max):
            raise BadRequestException(
                f"The value must be less than {self._max_value}. The actual value is {value}")

        return value


class IntValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) integer parameter values.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: int

    Usage: Let `validator = IntValidator(default_value=5)`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate(None) -> 5`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """

    _type = int

    def __init__(self, default_value=None, min_value=-math.inf, max_value=math.inf, include_min=True, include_max=True,
                 allowed_values=None, **kwargs):
        super().__init__(default_value=default_value, type=int, min_value=min_value, max_value=max_value,
                         include_min=include_min, include_max=include_max, allowed_values=allowed_values, **kwargs)
        self._type = int


class FloatValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) float parameter values.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: float

    Usage: Let `validator = FloatValidator(default_value=8)`, then
        * `validator.validate(5.5) -> 5.5`
        * `validator.validate(4.0) -> 4.0`
        * `validator.validate(4) -> 4.0`
        * `validator.validate('4') -> 4.0`
        * `validator.validate(None) -> 8.0`
        * `validator.validate(math.inf) -> math.inf`
        * `validator.validate('Infinity') -> math.inf`
        * `validator.validate('-Infinity') -> -math.nan`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate('inf') -> ValueError`
        * `validator.validate('infinity') -> ValueError`
        * `validator.validate('nan') -> ValueError`
    """

    _type = float

    def __init__(self, default_value=None, min_value=-math.inf, max_value=math.inf, include_min=True, include_max=True,
                 allowed_values=None, **kwargs):
        super().__init__(default_value=default_value, type=float, min_value=min_value, max_value=max_value,
                         include_min=include_min, include_max=include_max, allowed_values=allowed_values, **kwargs)
        self._type = float


class StrValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) string parameter values.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: str

    Usage:
        * Let `validator = StrValidator(default_value='foo')` then
            * `validator.validate('foo') -> 'foo'`
            * `validator.validate(None), 'foo'`
            * `validator.validate('false') -> 'false'`
            * `validator.validate(5) -> ValueError`
            * `validator.validate(True) -> ValueError`
        * Let `validator = StrValidator(default_value='8')` then
            * `validator.validate(None) -> '8'`
    """

    _type = str

    def __init__(self, default_value=None, allowed_values=None, **kwargs):
        super().__init__(default_value=default_value, type_=str, allowed_values=allowed_values, **kwargs)


class ListValidator(Validator):
    """
    Array validator.

    This validator allows validating serialized (or deserialized) array parameter values.
    A valid array is a serializable/deserializable list of (str, int, float, bool, array).

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: list

    Usage: Let `validator = ListValidator(default_value='[1,2,"foo"]')`, then
        * `validator.validate([5.5,3]) -> [5.5,3]`
        * `validator.validate('[5.5,3]') -> [5.5,3]`
        * `validator.validate('[5.5,3,["foo","bar"]]') -> [5.5,3,["foo","bar"]]`
        * `validator.validate('[5.5,3,{"foo":1.2}]') -> [5.5,3,{"foo":1.2}]`
        * `validator.validate(None) -> [1,2,"foo"]`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate(True) -> ValueError`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('5.5') -> ValueError`
        * `validator.validate('{"foo":1.2}') -> ValueError`
    """

    _type = list

    def __init__(self, default_value=None, **kwargs):
        super().__init__(default_value=default_value, type_=list, **kwargs)


class DictValidator(Validator):
    """
    Key-Value dictionnary validator.

    This validator allows validating serialized (or deserialized) JSON values.
    An valid JSON value is a serializable/deserializable key-value dictionnary.

    :property default_value: The default_value value returned by method :meth:`validate`
    :type default_value: dict

    Usage: Let `validator = DictValidator(default_value='{"foo":1.2}')`, then
        * `validator.validate(None), {"foo":1.2}`
        * `validator.validate('{"foo":0.5}') -> {"foo":0.5}`
        * `validator.validate('{"foo":0.5,"bar":[1,2,3]}') -> {"foo":0.5,"bar":[1,2,3]}`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate('True) -> ValueError`
        * `validator.validate(''false') -> ValueError`
        * `validator.validate(''5.5') -> ValueError`
        * `validator.validate('[5.5,3]') -> ValueError`
        * `validator.validate([5.5,3]) -> ValueError`
    """

    _type = dict

    def __init__(self, default_value=None, **kwargs):
        super().__init__(default_value=default_value, type_=dict, **kwargs)


class URLValidator(StrValidator):
    _type = URL

    def _validate(self, value):
        value = super()._validate(value)
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        valid = (re.match(regex, value) is not None)
        if valid == True:
            return value
        else:
            raise BadRequestException(f"The URL {value} is not valid")


class PathValidator(StrValidator):
    _type = Path

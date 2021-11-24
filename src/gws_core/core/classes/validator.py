# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math
import re
from typing import Any, Dict, List, Literal, Type, Union

from ..exception.exceptions import BadRequestException
from .path import URL, Path

ValidatorType = Literal["bool", "int", "float", "str", "list", "dict"]


class Validator:
    """
    Base validator class
    Base validator allows validating serialized (or deserialized) parameter values according to a
    `type`.

    Usage: This class should not be used as it, but rather use to implement validator subclasses.
    It provides the construction :meth:`from_specs` to create usable basic validators.

    :property type: The expected type of the value
    :type type: type
    """

    _type: Type = None
    _allowed_values: list = None

    _valid_types = ["bool", "int", "float", "str", "list", "dict"]

    def __init__(self, type_: ValidatorType = None, allowed_values: list = None):
        self.set_type(type_)

        if not allowed_values is None:
            if isinstance(allowed_values, list):
                self._allowed_values = allowed_values
            else:
                raise BadRequestException("The parameter allowed_values must be a list")

    def set_type(self, type_: Union[str, Type]) -> None:
        if type_ == bool or type_ == "bool":
            self._type = bool
        elif type_ == int or type_ == "int":
            self._type = int
        elif type_ == float or type_ == "float":
            self._type = float
        elif type_ == str or type_ == "str":
            self._type = str
        elif type_ == list or type_ == "list":
            self._type = list
        elif type_ == dict or type_ == "dict":
            self._type = dict
        else:
            raise BadRequestException("Invalid type")

    def validate(self, value: Union[bool, int, float, str, list, dict]) -> Any:
        """
        Valitates a value.

        Checks if the type of :param:value is a valid subtype of :property:type and that
        :param:value is serializable/deserilizable (using built-in Python methods :meth:`json.dumps`/:meth:`json.loads`).


        :param value: The value to validate
        :type value: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        :return: The validated value
        :rtype: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        """
        if value is None:
            return None

        value = self._validate(value)

        self._check_allowed_values(value)

        return value

    def _validate(self, value):
        if not isinstance(self._type, type):
            raise BadRequestException(
                f"The validator is not well configured. Invalid type {self._type}."
            )

        # If the value as the correct type
        if type(value) == self._type:
            return value

        if isinstance(value, str):
            value = self._from_str(value)

            if type(value) != self._type:
                raise BadRequestException(
                    f"The value {value} is of type {type(value)} but it expected a {self._type}"
                )

            return value
        else:
            raise BadRequestException(
                f"The value {value} is of type {type(value)} but it expected a {self._type}"
            )

    def _check_allowed_values(self, value: Any) -> None:
        """Check that the value is within the allow values if allowed value are provided"""
        if self._allowed_values is not None and len(self._allowed_values):
            if value in self._allowed_values:
                return
            else:
                raise BadRequestException(
                    f"Invalid value '{value}'. Allowed values are {self._allowed_values}"
                )

    def _from_str(self, str_value: str) -> Any:
        try:
            return json.loads(str_value)
        except:
            raise BadRequestException(f"Invalid value {str_value}")


class BoolValidator(Validator):
    """
    Validator class.

    This validator allows validating serialized (or deserialized) boolean parameter values.

    Usage: Let `validator = BoolValidator()`, then
        * `validator.validate(False) -> False`
        * `validator.validate(True) -> True`
        * `validator.validate('true') -> True`
        * `validator.validate('false') -> False`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate(4) -> ValueError`
    """

    def __init__(self):
        super().__init__(type_=bool, allowed_values=None)


class NumericValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) numerical parameter values.


    Usage: Let `validator = IntValidator()`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """

    _min_value = None
    _max_value = None
    _include_min = True
    _include_max = True

    def __init__(
        self,
        type_=float,
        min_value=-math.inf,
        max_value=math.inf,
        include_min=False,
        include_max=False,
        allowed_values: list = None,
    ):

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

        super().__init__(type_=type_, allowed_values=allowed_values)

    def _validate(self, value):
        if (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and self._type in (int, float)
        ):
            is_valid = self._type(value) == value
            if not is_valid:
                raise BadRequestException(
                    f"The value {value} cannot be casted to the class {self._type} with floating point alteration."
                )

            value = self._type(value)

        value = super()._validate(value)

        if value < self._min_value or (
            value == self._min_value and not self._include_min
        ):
            raise BadRequestException(
                f"The value must be greater than {self._min_value}. The actual value is {value}"
            )

        if value > self._max_value or (
            value == self._max_value and not self._include_max
        ):
            raise BadRequestException(
                f"The value must be less than {self._max_value}. The actual value is {value}"
            )

        return value

    def _from_str(self, str_value: str) -> Any:
        value = super()._from_str(str_value)

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise BadRequestException(
                f"Expected a numeric value but got a '{type(value)}'"
            )

        is_valid = math.isnan(value) or (self._type(value) == value)
        if not is_valid:
            raise BadRequestException(
                f"The value {value} cannot be casted to the class {self._type} with floating point alteration."
            )

        return self._type(value)


class IntValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) integer parameter values.

    Usage: Let `validator = IntValidator()`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """

    def __init__(
        self,
        min_value=-math.inf,
        max_value=math.inf,
        include_min=True,
        include_max=True,
        allowed_values: List[int] = None,
    ):
        super().__init__(
            type_=int,
            min_value=min_value,
            max_value=max_value,
            include_min=include_min,
            include_max=include_max,
            allowed_values=allowed_values,
        )
        self._type = int


class FloatValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) float parameter values.

    Usage: Let `validator = FloatValidator()`, then
        * `validator.validate(5.5) -> 5.5`
        * `validator.validate(4.0) -> 4.0`
        * `validator.validate(4) -> 4.0`
        * `validator.validate('4') -> 4.0`
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

    def __init__(
        self,
        min_value=-math.inf,
        max_value=math.inf,
        include_min=True,
        include_max=True,
        allowed_values: List[float] = None,
    ):
        super().__init__(
            type_=float,
            min_value=min_value,
            max_value=max_value,
            include_min=include_min,
            include_max=include_max,
            allowed_values=allowed_values,
        )
        self._type = float


class StrValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) string parameter values.

    Usage:
        * Let `validator = StrValidator()` then
            * `validator.validate('foo') -> 'foo'`
            * `validator.validate('false') -> 'false'`
            * `validator.validate(5) -> ValueError`
            * `validator.validate(True) -> ValueError`
    """

    _min_length = -1
    _max_length = math.inf

    def __init__(self, allowed_values: List[str] = None, min_length: int = None, max_length: int = None):
        super().__init__(type_=str, allowed_values=allowed_values, )

        if min_length is not None:
            if isinstance(min_length, str):
                min_length = int(min_length)
            if not isinstance(min_length, (int, float)):
                raise BadRequestException("The min_length must be a numeric")
            min_length = max(-1, min_length)
            self._min_length = min_length

        if max_length is not None:
            if isinstance(max_length, str):
                max_length = int(max_length)
            if not isinstance(max_length, (int, float)):
                raise BadRequestException("The max_length must be a numeric")
            max_length = min(math.inf, max_length)
            self._max_length = max_length

        if self._min_length > self._max_length:
            raise BadRequestException(
                f"The min length ({self._min_length}) must be grater than the max length ({self._max_length})")

    def _from_str(self, str_value: str) -> str:
        return str_value

    def _validate(self, value) -> str:
        value: str = super()._validate(value)
        if len(value) < self._min_length:
            raise BadRequestException(
                f"The string length is {len(value)}. It is less than the min length of {self._min_length}")
        if len(value) > self._max_length:
            raise BadRequestException(
                f"The string length is {len(value)}. It exceeds the max length of {self._min_length}")
        return value


class ListValidator(Validator):
    """
    Array validator.

    This validator allows validating serialized (or deserialized) array parameter values.
    A valid array is a serializable/deserializable list of (str, int, float, bool, array).

    Usage: Let `validator = ListValidator()`, then
        * `validator.validate([5.5,3]) -> [5.5,3]`
        * `validator.validate('[5.5,3]') -> [5.5,3]`
        * `validator.validate('[5.5,3,["foo","bar"]]') -> [5.5,3,["foo","bar"]]`
        * `validator.validate('[5.5,3,{"foo":1.2}]') -> [5.5,3,{"foo":1.2}]`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate(True) -> ValueError`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('5.5') -> ValueError`
        * `validator.validate('{"foo":1.2}') -> ValueError`
    """

    must_be_deep_jsonable: bool
    min_number_of_occurrences: int = True
    max_number_of_occurrences: int = True

    def __init__(
            self, must_be_deep_jsonable=True, min_number_of_occurrences: int = -1, max_number_of_occurrences: int = -1,
            allowed_values: list = None):
        super().__init__(type_=list, allowed_values=allowed_values)
        self.must_be_deep_jsonable = must_be_deep_jsonable
        self.min_number_of_occurrences = min_number_of_occurrences
        self.max_number_of_occurrences = max_number_of_occurrences

    def _validate(self, value):
        value: List = super()._validate(value)

        # Check if the value is serializable
        if self.must_be_deep_jsonable:
            if not self.is_deep_jsonnable(value):
                raise BadRequestException(f"The value {value} is not serializable.")

        if self.min_number_of_occurrences >= 0 and len(value) < self.min_number_of_occurrences:
            raise BadRequestException(
                f"The list contains {len(value)} elements but the minimum number of elements is {self.min_number_of_occurrences}.")

        if self.max_number_of_occurrences >= 0 and len(value) > self.max_number_of_occurrences:
            raise BadRequestException(
                f"The list contains {len(value)} elements but the maximum number of elements is {self.max_number_of_occurrences}.")

        return value

    def is_deep_jsonnable(self, value: List) -> bool:
        try:
            json.loads(json.dumps(value))
            return True
        except:
            return False


class DictValidator(Validator):
    """
    Key-Value dictionnary validator.

    This validator allows validating serialized (or deserialized) JSON values.
    An valid JSON value is a serializable/deserializable key-value dictionnary.

    Usage: Let `validator = DictValidator()`, then
        * `validator.validate('{"foo":0.5}') -> {"foo":0.5}`
        * `validator.validate('{"foo":0.5,"bar":[1,2,3]}') -> {"foo":0.5,"bar":[1,2,3]}`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate('True) -> ValueError`
        * `validator.validate(''false') -> ValueError`
        * `validator.validate(''5.5') -> ValueError`
        * `validator.validate('[5.5,3]') -> ValueError`
        * `validator.validate([5.5,3]) -> ValueError`
    """

    must_be_deep_jsonable = True

    def __init__(self, must_be_deep_jsonable=True):
        super().__init__(type_=dict, allowed_values=None)
        self.must_be_deep_jsonable = must_be_deep_jsonable

    def _validate(self, value):
        value: Dict = super()._validate(value)

        # Check if the value is jsonable
        if self.must_be_deep_jsonable:
            if not self.is_deep_jsonnable(value):
                raise BadRequestException(f"The value {value} is not serializable.")

        return value

    def is_deep_jsonnable(self, value: List) -> bool:
        try:
            json.loads(json.dumps(value))
            return True
        except:
            return False


class URLValidator(StrValidator):
    _type = URL

    def _validate(self, value):
        value = super()._validate(value)
        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            # domain...
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        valid = re.match(regex, value) is not None
        if valid == True:
            return value
        else:
            raise BadRequestException(f"The URL {value} is not valid")


class PathValidator(StrValidator):
    _type = Path

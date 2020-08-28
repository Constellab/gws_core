
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math
from gws.logger import Logger

class Validator:
    """
    Base validator class

    Base validator allows validating serialized (or deserialized) parameter values according to a
    `type`.

    :property default: The default value returned by method :meth:`validate`
    :type default: any
    :property type: The expected type of the value
    :type type: type

    Usage: This class should not be used as it, but rather use to implement validator subclasses. 
    It provides the construction :meth:`from_type` to create usable basic validators. 
    
    For example:
        * `Validator.from_type(int, default=5) -> IntegerValidator(default=5)`
        * `Validator.from_type(bool, default=True) -> BooleanValidator(default=True)`
        * `Validator.from_type(float, default=5.5) -> FloatValidator(default=5.5)`
        * `Validator.from_type(str, default='foo') -> CharValidator(default='foo')`
        * `Validator.from_type(list, default=[1,"foo"]) -> ArrayValidator(default=[1,"foo"])`
        * `Validator.from_type(dict, default={"foo":1}) -> JSONValidator(default={"foo":1})`
    """

    _type = None
    _default = None
    _valid_types = ['bool', 'int', 'float', 'str', 'list', 'dict']

    def __init__(self, default=None, type=None):
        if not type is None:
            self._type = type
        
        if not default is None:
            try:
                self._default = self._validate(default)
            except Exception as err:
                Logger.error(Exception(f"The default value is not valid. Error message: {err}"))
    
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
            Logger.error(Exception(f"Invalid type"))

    def validate(self, value: (bool, int, float, str, list, dict)) -> (bool, int, float, str, list, dict):
        """
        Valitates a value.
        
        Checks if the type of :param:`value` is a valid subtype of :property:`type` and that
        :param:`value` is serializable/deserilizable (using built-in Python methods :meth:`json.dumps`/:meth:`json.loads`).

        :param value: The value to validate
        :type value: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        :return: The validated value
        :rtype: An instance of `bool`, `int`, `float`, `str` or serilaizable `list`, `dict`
        :Logger.error(`Exception`: If the :param:`value` is not valid)

        Usage:
            * `Validator.from_type(int, default=5) -> IntegerValidator(default=5)`
            * `Validator.from_type(bool, default=True) -> BooleanValidator(default=True)`
            * `Validator.from_type(float, default=5.5) -> FloatValidator(default=5.5)`
            * `Validator.from_type(str, default='foo') -> CharValidator(default='foo')`
            * `Validator.from_type(list, default=[1,"foo"]) -> ArrayValidator(default=[1,"foo"])`
            * `Validator.from_type(dict, default={"foo":1}) -> JSONValidator(default={"foo":1})`
        """
        if value is None:
            value = self._default
        
        if value is None:
            return value

        return self._validate(value)
    
    def _validate(self, value):
        
        if not isinstance(self.type, type):
            Logger.error(ValueError(f"The validator is not well configured. Invalid type {self.type}."))
        
        if type(value) == self.type:
            if isinstance(value, (list,dict,)):
                try:
                    is_serilizable = (json.loads(json.dumps(value)) == value)
                except:
                    is_serilizable = False
                
                if not is_serilizable:
                    Logger.error(ValueError(f"The value {value} is not serializable."))

            return value
        else:
            is_maybe_convertible_without_floating_error =   not isinstance(value, bool) and \
                                                            isinstance(value, (int,float,)) and self.type in (int,float,)
            if is_maybe_convertible_without_floating_error:
                is_valid = (self.type(value) == value)
                if not is_valid:
                    Logger.error(ValueError(f"The value {value} cannot be casted to the class {self.type} with floating point alteration."))
                
                return self.type(value)

        if isinstance(value, str):
            try:
                value = json.loads(value)
                is_maybe_convertible_without_floating_error =   not isinstance(value, bool) and \
                                                                isinstance(value, (int,float,)) and self.type in (int,float,)
                if is_maybe_convertible_without_floating_error:
                    is_valid = math.isnan(value) or (self.type(value) == value)
                    if not is_valid:
                        Logger.error(ValueError(f"The value {value} cannot be casted to the class {self.type} with floating point alteration."))
                    
                    return self.type(value)
                elif type(value) != self.type:
                    Logger.error(ValueError(f"The deserialized value must be an instance of {self.type}. The actual deserialized value is {value}."))

            except:
                Logger.error(ValueError("The value cannot be deserialized. Please give a valid serialized string value"))

            return value
        else:
            Logger.error(ValueError(f"Invalid value {value}"))

    @staticmethod
    def from_type(type, default = None, **kwargs) -> 'Validator':
        """
        Constructs usable basic validators.

        :param type: The type used for validation
        :type type: `type` or `str` in built-in types `bool`, `int`, `float`, `str`, `list`, `dict`
        :param default: The default value to return, Defaults to `None`
        :type default: any, An instance of :param:`type`
        :return: The Validator corresponding to the :param:`type`
        :rtype: subclass of `Validator`
        :Logger.error(`Exception`: If the :param:`type` is not valid or the the type if :param:`default` is not equal to :param:`type`)

        Usage:
            * `Validator.from_type('int', default=5) -> IntegerValidator(default=5)`
            * `Validator.from_type(int, default=5) -> IntegerValidator(default=5)`
            * `Validator.from_type('bool', default=True) -> BooleanValidator(default=True)`
            * `Validator.from_type(bool, default=True) -> BooleanValidator(default=True)`
            * `Validator.from_type('float', default=5.5) -> FloatValidator(default=5.5)`
            * `Validator.from_type('str', default='foo') -> CharValidator(default='foo')`
            * `Validator.from_type('list', default=[1,"foo"]) -> ArrayValidator(default=[1,"foo"])`
            * `Validator.from_type('dict', default={"foo":1}) -> JSONValidator(default={"foo":1})`
        """

        if type == bool or type == 'bool':
            return BooleanValidator(default=default, **kwargs)
        elif type == int or type == 'int':
            return IntegerValidator(default=default, **kwargs)
        elif type == float or type == 'float':
            return FloatValidator(default=default, **kwargs)
        elif type == str or type == 'str':
            return CharValidator(default=default, **kwargs)
        elif type == list or type == 'list':
            return ArrayValidator(default=default, **kwargs)
        elif type == dict or type == 'dict':
            return JSONValidator(default=default, **kwargs)
        else:
            Logger.error(Exception("Invalid type. Valid types are (bool, int, float, str, list, dict)."))

class BooleanValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) boolean parameter values.

    :property default: The default value returned by method :meth:`validate`
    :type default: bool

    Usage: Let `validator = BooleanValidator(default=True)`, then
        * `validator.validate(False) -> False`
        * `validator.validate(True) -> True`
        * `validator.validate(None) -> True if defaults to True`
        * `validator.validate('true') -> True`
        * `validator.validate('false') -> False`
        * `validator.validate('foo') -> ValueError`
        * `validator.validate(4) -> ValueError`
    """
    _type = bool

    def __init__(self, default=None):
        super().__init__(default=default, type=bool)

class NumericValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) numerical parameter values.

    :property default: The default value returned by method :meth:`validate`
    :type default: int
    :property min: The default value returned by method :meth:`validate`
    :type min: int
    :property max: The default value returned by method :meth:`validate`
    :type max: int

    Usage: Let `validator = IntegerValidator(default=5)`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate(None) -> 5`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """
    _min = None
    _max = None
    _include_min = True
    _include_max = True

    def __init__(self, default=None, type=float, min=-math.inf, max=math.inf, include_min=False, include_max=False):
        self._min = min
        self._max = max
        self._include_min = include_min
        self._include_max = include_max
        if math.isfinite(self._min):
            self._include_min = True
        
        if math.isfinite(self._max):
            self._include_max = True

        super().__init__(default=default, type=type)
 
    def _validate(self, value):
        value = super()._validate(value)

        if value < self._min or (value == self._min and not self._include_min):
            Logger.error(ValueError(f"The value must be greater than {self._min}. The actual value is {value}"))

        if value > self._max or (value == self._max and not self._include_max):
            Logger.error(ValueError(f"The value must be less than {self._max}. The actual value is {value}"))
        
        return value

class IntegerValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) integer parameter values.

    :property default: The default value returned by method :meth:`validate`
    :type default: int

    Usage: Let `validator = IntegerValidator(default=5)`, then
        * `validator.validate('3') -> 3`
        * `validator.validate(3) -> 3)`
        * `validator.validate(3.0) -> 3`
        * `validator.validate(None) -> 5`
        * `validator.validate('false') -> ValueError`
        * `validator.validate('true') -> ValueError`
        * `validator.validate('foo') -> ValueError`
    """
    _type = int
    
    def __init__(self, default=None, min=-math.inf, max=math.inf, include_min=True, include_max=True):
        super().__init__(default=default, type=int, min=min, max=max, include_min=include_min, include_max=include_max)
        self._type = int

class FloatValidator(NumericValidator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) float parameter values.

    :property default: The default value returned by method :meth:`validate`
    :type default: float

    Usage: Let `validator = FloatValidator(default=8)`, then
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
    
    def __init__(self, default=None, min=-math.inf, max=math.inf, include_min=True, include_max=True):
        super().__init__(default=default, type=float, min=min, max=max, include_min=include_min, include_max=include_max)
        self._type = float

class CharValidator(Validator):
    """
    Validator class

    This validator allows validating serialized (or deserialized) string parameter values.

    :property default: The default value returned by method :meth:`validate`
    :type default: str

    Usage: 
        * Let `validator = CharValidator(default='foo')` then
            * `validator.validate('foo') -> 'foo'`
            * `validator.validate(None), 'foo'`
            * `validator.validate('false') -> 'false'`
            * `validator.validate(5) -> ValueError`
            * `validator.validate(True) -> ValueError`
        * Let `validator = CharValidator(default='8')` then
            * `validator.validate(None) -> '8'`
    """
    _type = str
    
    def __init__(self, default = None):
        super().__init__(default=default, type=str)

class ArrayValidator(Validator):
    """
    Array validator. 
    
    This validator allows validating serialized (or deserialized) array parameter values.
    A valid array is a serializable/deserializable list of (str, int, float, bool, array).
    
    :property default: The default value returned by method :meth:`validate`
    :type default: list

    Usage: Let `validator = ArrayValidator(default='[1,2,"foo"]')`, then
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
    
    def __init__(self, default=None):
        super().__init__(default=default, type=list)

class JSONValidator(Validator):
    """
    Key-Value dictionnary validator.

    This validator allows validating serialized (or deserialized) JSON values.
    An valid JSON value is a serializable/deserializable key-value dictionnary.
    
    :property default: The default value returned by method :meth:`validate`
    :type default: dict

    Usage: Let `validator = JSONValidator(default='{"foo":1.2}')`, then
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
    
    def __init__(self, default=None):
        super().__init__(default=default, type=dict)


from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from ..core.classes.validator import (BoolValidator, DictValidator,
                                      FloatValidator, IntValidator,
                                      ListValidator, StrValidator, Validator)

ParamSpecType = TypeVar('ParamSpecType')


class ParamSpec(Generic[ParamSpecType]):
    """Main abstract class for the spec of config params

    :param Generic: [description]
    :type Generic: [type]
    :return: [description]
    :rtype: [type]
    """

    # Default value, if None, and optional is false, the config is mandatory
    # If a value is provided there is no need to set the optional
    # Setting optional to True, allows default None value
    default_value: Optional[ParamSpecType]
    optional: bool

    # Description of the param, showed in the interface
    description: Optional[str]

    # Measure unit of the value (ex kg)
    unit: Optional[str]

    def __init__(self, default_value: Optional[ParamSpecType] = None, optional: bool = False,
                 description: Optional[str] = None, unit: Optional[str] = None) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory
                        If a value is provided there is no need to set the optional
                        Setting optional to True, allows default None value
        :param optional: See default value
        :type optional: Optional[str]
        :type default: Optional[ConfigParamType]
        :param description: Description of the param, showed in the interface
        :type description: Optional[str]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        self.default_value = default_value
        self.description = description
        self.unit = unit

        # the param is optional if the default value is set or optional is set to True
        self.optional = default_value is not None or optional

    def check_default_value(self) -> None:
        if self.default_value is None:
            return

        self.default_value = self.validate(self.default_value)

    def get_and_check_default_value(self) -> ParamSpecType:
        self.check_default_value()
        return self.default_value

    @abstractmethod
    def get_type(self) -> Type[ParamSpecType]:
        pass

    @abstractmethod
    def get_validator(self) -> Validator:
        pass

    @classmethod
    def empty(cls) -> 'ParamSpec':
        return cls()

    def load_from_json(self, json_:  Dict[str, Any]) -> None:
        self.default_value = json_.get("default_value")
        self.optional = json_.get("optional")
        self.description = json_.get("description")
        self.unit = json_.get("unit")

    def to_json(self) -> Dict[str, Any]:
        _json: Dict[str, Any] = {
            "type": self.get_type().__name__,
            "optional": self.optional
        }

        if self.default_value is not None:
            _json["default_value"] = self.default_value
        if self.description is not None:
            _json["description"] = self.description
        if self.unit is not None:
            _json["unit"] = self.unit
        return _json

    def validate(self, value: Any) -> ParamSpecType:
        return self.get_validator().validate(value)


class StrParam(ParamSpec[str]):
    """String param
    """

    #  If present, the value must be in the array
    allowed_values: Optional[List[str]]

    def __init__(
            self, default_value: Optional[str] = None, optional: bool = False,
            description: Optional[str] = None,
            allowed_values: Optional[List[str]] = None, unit: Optional[str] = None) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory
                        If a value is provided there is no need to set the optional
                        Setting optional to True, allows default None value
        :param optional: See default value
        :type optional: Optional[str]
        :param description: Description of the param, showed in the interface
        :type description: Optional[str]
        :param allowed_values: If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        super().__init__(default_value=default_value, optional=optional, description=description, unit=unit)
        self.allowed_values = allowed_values

    @abstractmethod
    def get_type(self) -> Type[str]:
        return str

    def get_validator(self) -> Validator:
        return StrValidator(default_value=self.default_value, allowed_values=self.allowed_values)

    def load_from_json(self, json_:  Dict[str, Any]) -> None:
        super().load_from_json(json_)
        self.allowed_values = json_.get("allowed_values")

    def to_json(self) -> Dict[str, Any]:
        json_: Dict[str, Any] = super().to_json()
        if self.allowed_values:
            json_["allowed_values"] = self.allowed_values
        return json_


class BoolParam(ParamSpec[bool]):
    """Boolean param
    """
    @abstractmethod
    def get_type(self) -> Type[bool]:
        return bool

    def get_validator(self) -> Validator:
        return BoolValidator(default_value=self.default_value)


class DictParam(ParamSpec[dict]):
    """Any json dict param
    """

    @abstractmethod
    def get_type(self) -> Type[dict]:
        return dict

    def get_validator(self) -> Validator:
        return DictValidator(default_value=self.default_value)


class ListParam(ParamSpec[list]):
    """Any list param
    """

    @abstractmethod
    def get_type(self) -> Type[list]:
        return list

    def get_validator(self) -> Validator:
        return ListValidator(default_value=self.default_value)


class NumericParam(ParamSpec[ParamSpecType], Generic[ParamSpecType]):
    """Abstract numerci param class (int or float)
    """

    # If present, the value must be in the array
    allowed_values: Optional[List[ParamSpecType]]

    # The minimum value allowed (including)
    min_value: Optional[ParamSpecType]

    # The maximum value allowed (including)
    max_value: Optional[ParamSpecType]

    def __init__(
            self, default_value: Optional[ParamSpecType] = None,
            optional: bool = False,
            description: Optional[str] = None,
            allowed_values: Optional[List[ParamSpecType]] = None,
            min_value: Optional[ParamSpecType] = None,
            max_value: Optional[ParamSpecType] = None,
            unit: Optional[str] = None) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory
                        If a value is provided there is no need to set the optional
                        Setting optional to True, allows default None value
        :param optional: See default value
        :type optional: Optional[str]
        :param description: Description of the param, showed in the interface
        :type description: Optional[str]
        :param allowed_values: If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param min: # The minimum value allowed (including)
        :type min:  Optional[ConfigParamType]
        :param max: # The maximum value allowed (including)
        :type max:  Optional[ConfigParamType]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        super().__init__(default_value=default_value, optional=optional, description=description, unit=unit)
        self.allowed_values = allowed_values
        self.min_value = min_value
        self.max_value = max_value

    @abstractmethod
    def get_type(self) -> Type[ParamSpecType]:
        pass

    @abstractmethod
    def get_validator(self) -> Validator:
        pass

    def load_from_json(self, json_:  Dict[str, Any]) -> None:
        super().load_from_json(json_)
        self.allowed_values = json_.get("allowed_values")
        self.min_value = json_.get("min_value")
        self.max_value = json_.get("max_value")

    def to_json(self) -> Dict[str, Any]:
        json_: Dict[str, Any] = super().to_json()

        if self.allowed_values:
            json_["allowed_values"] = self.allowed_values
        if self.min_value:
            json_["min_value"] = self.min_value
        if self.max_value:
            json_["max_value"] = self.max_value

        return json_


class IntParam(NumericParam[int]):
    """int param
    """

    def get_type(self) -> Type[int]:
        return int

    def get_validator(self) -> Validator:
        return IntValidator(default_value=self.default_value, allowed_values=self.allowed_values,
                            min_value=self.min_value, max_value=self.max_value)


class FloatParam(NumericParam[float]):
    """int param
    """

    def get_type(self) -> Type[float]:
        return float

    def get_validator(self) -> Validator:
        return FloatValidator(default_value=self.default_value, allowed_values=self.allowed_values,
                              min_value=self.min_value, max_value=self.max_value)

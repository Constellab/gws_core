
from abc import abstractmethod
from typing import Any, Dict, Generic, List, Literal, Optional, Type, TypeVar

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..core.classes.validator import (BoolValidator, DictValidator,
                                      FloatValidator, IntValidator,
                                      ListValidator, StrValidator, Validator)

ParamSpecType = TypeVar('ParamSpecType')


# Visibility of a param
# Public --> main param visible in the first config section in the interface
# Protected --> considered as advanced param, it will be in the advanced section in the interface (it must have a default value or be optional)
# Public --> private param, it will not be visible in the interface (it must have a default value or be optional)
ParamSpecVisibilty = Literal["public", "protected", "private"]


class ParamSpec(Generic[ParamSpecType]):
    """Main abstract class for the spec of config params
    """

    # Default value, if None, and optional is false, the config is mandatory
    # If a value is provided there is no need to set the optional
    # Setting optional to True, allows default None value
    default_value: Optional[ParamSpecType]
    optional: bool

    # Visibility of the param, see doc on type ParamSpecVisibilty for more info
    visibility: ParamSpecVisibilty

    # Human readable name of the param, showed in the interface
    human_name: Optional[str]

    # Description of the param, showed in the interface
    short_description: Optional[str]

    # Measure unit of the value (ex kg)
    unit: Optional[str]

    def __init__(self, default_value: Optional[ParamSpecType] = None, optional: bool = False,
                 visibility: ParamSpecVisibilty = 'public',
                 human_name: Optional[str] = None, short_description: Optional[str] = None,
                 unit: Optional[str] = None) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory
                        If a value is provided there is no need to set the optional
                        Setting optional to True, allows default None value
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        self._check_visibility(visibility)
        self.visibility = visibility
        self.human_name = human_name
        self.short_description = short_description
        self.unit = unit

        # the param is optional if the default value is set or optional is set to True
        self.optional = default_value is not None or optional

        # If the visibility is not public, the param must have a default value
        if self.visibility != 'public' and not self.optional:
            raise BadRequestException(
                f"The '{self.get_type()}' parame visibility is set to {self.visibility} but the param is mandatory. It must have a default value of be optional")

        self.default_value = self.validate(default_value)

    def get_default_value(self) -> ParamSpecType:
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
        self.human_name = json_.get("human_name")
        self.short_description = json_.get("short_description")
        self.unit = json_.get("unit")

    def to_json(self) -> Dict[str, Any]:
        _json: Dict[str, Any] = {
            "type": self.get_type().__name__,
            "optional": self.optional
        }

        if self.default_value is not None:
            _json["default_value"] = self.default_value
        if self.human_name is not None:
            _json["human_name"] = self.human_name
        if self.short_description is not None:
            _json["short_description"] = self.short_description
        if self.unit is not None:
            _json["unit"] = self.unit
        return _json

    def validate(self, value: Any) -> ParamSpecType:
        if value is None:
            return None

        return self.get_validator().validate(value)

    def _check_visibility(self, visibility: ParamSpecVisibilty) -> None:
        allowed_visibility: List[ParamSpecVisibilty] = ['public', 'protected', 'private']
        if visibility not in allowed_visibility:
            raise BadRequestException(
                f"The visibilty '{visibility}' of the '{self.get_type()}' is incorrect. It must be one of the following values : {str(allowed_visibility)}")


class StrParam(ParamSpec[str]):
    """String param
    """

    #  If present, the value must be in the array
    allowed_values: Optional[List[str]]

    def __init__(
            self, default_value: Optional[str] = None,
            optional: bool = False,
            visibility: ParamSpecVisibilty = 'public',
            human_name: Optional[str] = None,
            short_description: Optional[str] = None,
            allowed_values: Optional[List[str]] = None,
            unit: Optional[str] = None) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory
                        If a value is provided there is no need to set the optional
                        Setting optional to True, allows default None value
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param allowed_values: If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        self.allowed_values = allowed_values
        super().__init__(default_value=default_value, optional=optional,
                         visibility=visibility, human_name=human_name, short_description=short_description, unit=unit)

    def get_type(self) -> Type[str]:
        return str

    def get_validator(self) -> Validator:
        return StrValidator(allowed_values=self.allowed_values)

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

    def get_type(self) -> Type[bool]:
        return bool

    def get_validator(self) -> Validator:
        return BoolValidator()


class DictParam(ParamSpec[dict]):
    """Any json dict param
    """

    def get_type(self) -> Type[dict]:
        return dict

    def get_validator(self) -> Validator:
        return DictValidator()


class ListParam(ParamSpec[list]):
    """Any list param
    """

    def get_type(self) -> Type[list]:
        return list

    def get_validator(self) -> Validator:
        return ListValidator()


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
            visibility: ParamSpecVisibilty = 'public',
            human_name: Optional[str] = None,
            short_description: Optional[str] = None,
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
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param allowed_values: If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param min: # The minimum value allowed (including)
        :type min:  Optional[ConfigParamType]
        :param max: # The maximum value allowed (including)
        :type max:  Optional[ConfigParamType]
        :param unit: Measure unit of the value (ex kg)
        :type unit: Optional[str]
        """
        self.allowed_values = allowed_values
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(default_value=default_value, optional=optional,
                         visibility=visibility, human_name=human_name, short_description=short_description, unit=unit)

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
        return IntValidator(allowed_values=self.allowed_values,
                            min_value=self.min_value, max_value=self.max_value)


class FloatParam(NumericParam[float]):
    """int param
    """

    def get_type(self) -> Type[float]:
        return float

    def get_validator(self) -> Validator:
        return FloatValidator(allowed_values=self.allowed_values,
                              min_value=self.min_value, max_value=self.max_value)

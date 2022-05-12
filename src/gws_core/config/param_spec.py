# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from gws_core.core.utils.logger import Logger

from ..core.classes.validator import (BoolValidator, DictValidator,
                                      FloatValidator, IntValidator,
                                      ListValidator, StrValidator, Validator)
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .param_types import ParamSpecDict, ParamSpecVisibilty

ParamSpecType = TypeVar("ParamSpecType")


class ParamSpec(Generic[ParamSpecType]):
    """Main abstract class for the spec of config params"""

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

    PUBLIC_VISIBILITY = "public"
    PROTECTED_VISIBILITY = "protected"
    PRIVATE_VISIBILITY = "private"
    MAX_ALLOWED_VALUES_COUNT = 50

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
        unit: Optional[str] = None,
    ) -> None:
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
        self.visibility = visibility
        self.human_name = human_name
        self.short_description = short_description
        self.unit = unit

        # the param is optional if the default value is set or optional is set to True
        self.optional = default_value is not None or optional
        self._check_visibility(visibility)

        self.default_value = self.validate(default_value)

    def get_default_value(self) -> ParamSpecType:
        return self.default_value

    @abstractmethod
    def _get_validator(self) -> Validator:
        pass

    def to_json(self) -> ParamSpecDict:
        _json: ParamSpecDict = {
            "type": self.get_str_type(),
            "optional": self.optional,
            "visibility": self.visibility,
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

        return self._get_validator().validate(value)

    def _check_visibility(self, visibility: ParamSpecVisibilty) -> None:
        allowed_visibility: List[ParamSpecVisibilty] = [
            "public",
            "protected",
            "private",
        ]
        if visibility not in allowed_visibility:
            raise BadRequestException(
                f"The visibilty '{visibility}' of the '{self.get_str_type()}' param is incorrect. It must be one of the following values : {str(allowed_visibility)}"
            )

        # If the visibility is not public, the param must have a default value
        if self.visibility != "public" and not self.optional:
            raise BadRequestException(
                f"The '{self.get_str_type()}' param visibility is set to {self.visibility} but the param is mandatory. It must have a default value of be optional if the visiblity is not public"
            )

    ################################# CLASS METHODS ###############################

    @classmethod
    @abstractmethod
    def get_str_type(cls) -> str:
        pass

    @classmethod
    def empty(cls) -> "ParamSpec":
        return cls()

    @classmethod
    def create_from_json(cls, json_: Dict[str, Any]) -> "ParamSpec":
        config_param_type: Type[ParamSpec] = cls._get_param_spec_class_type(json_["type"])
        return config_param_type.load_from_json(json_)

    @classmethod
    def load_from_json(cls, json_: Dict[str, Any]) -> "ParamSpec":
        param_spec = cls.empty()
        param_spec.default_value = json_.get("default_value")
        param_spec.optional = json_.get("optional")
        param_spec.human_name = json_.get("human_name")
        param_spec.short_description = json_.get("short_description")
        param_spec.unit = json_.get("unit")
        param_spec.visibility = json_.get("visibility")
        return param_spec

    @classmethod
    def _get_param_spec_class_type(cls, type_: str) -> Type["ParamSpec"]:
        """Get the class type of ConfigParam base on type
        """
        if type_ == 'bool':
            return BoolParam
        elif type_ == 'int':
            return IntParam
        elif type_ == 'float':
            return FloatParam
        elif type_ == 'str':
            return StrParam
        elif type_ == 'list':
            return ListParam
        # elif type_ == 'dict':
        #     return DictParam
        elif type_ == 'param_set':
            from .param_set import ParamSet
            return ParamSet
        else:
            raise BadRequestException("Invalid type")


class StrParam(ParamSpec[str]):
    """String param"""

    #  If present, the value must be in the array
    allowed_values: Optional[List[str]]
    min_length: Optional[int]
    max_length: Optional[int]

    def __init__(
        self,
        default_value: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
        allowed_values: Optional[List[str]] = None,
        unit: Optional[str] = None,
    ) -> None:
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
        if allowed_values is not None and isinstance(allowed_values, list):
            if len(allowed_values) > self.MAX_ALLOWED_VALUES_COUNT:
                Logger.warning(
                    f'[ParamSpecs] Max number of allowed value reached, values will be truncated. Max {self.MAX_ALLOWED_VALUES_COUNT}')
            self.allowed_values = allowed_values[:self.MAX_ALLOWED_VALUES_COUNT]
        else:
            self.allowed_values = None

        self.min_length = min_length
        self.max_length = max_length
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            unit=unit,
        )

    def _get_validator(self) -> Validator:
        return StrValidator(
            allowed_values=self.allowed_values,
            min_length=self.max_length,
            max_length=self.max_length
        )

    def to_json(self) -> ParamSpecDict:
        json_: ParamSpecDict = super().to_json()
        if self.allowed_values:
            json_["allowed_values"] = self.allowed_values
        return json_

    @classmethod
    def get_str_type(cls) -> str:
        return 'str'

    @classmethod
    def load_from_json(cls, json_: Dict[str, Any]) -> "StrParam":
        param_spec: StrParam = super().load_from_json(json_)
        param_spec.allowed_values = json_.get("allowed_values")
        return param_spec


class BoolParam(ParamSpec[bool]):
    """Boolean param"""

    def _get_validator(self) -> Validator:
        return BoolValidator()

    @classmethod
    def get_str_type(cls) -> str:
        return 'bool'


class DictParam(ParamSpec[dict]):
    """Any json dict param"""

    def _get_validator(self) -> Validator:
        return DictValidator()

    @classmethod
    def get_str_type(cls) -> str:
        return 'dict'


class ListParam(ParamSpec[list]):
    """Any list param"""

    def _get_validator(self) -> Validator:
        return ListValidator()

    @classmethod
    def get_str_type(cls) -> str:
        return 'list'


class NumericParam(ParamSpec[ParamSpecType], Generic[ParamSpecType]):
    """Abstract numerci param class (int or float)"""

    # If present, the value must be in the array
    allowed_values: Optional[List[ParamSpecType]]

    # The minimum value allowed (including)
    min_value: Optional[ParamSpecType]

    # The maximum value allowed (including)
    max_value: Optional[ParamSpecType]

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
        allowed_values: Optional[List[ParamSpecType]] = None,
        min_value: Optional[ParamSpecType] = None,
        max_value: Optional[ParamSpecType] = None,
        unit: Optional[str] = None,
    ) -> None:
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
        if allowed_values is not None and isinstance(allowed_values, list):
            if len(allowed_values) > self.MAX_ALLOWED_VALUES_COUNT:
                Logger.warning(
                    f'[ParamSpecs] Max number of allowed value reached, values will be truncated. Max {self.MAX_ALLOWED_VALUES_COUNT}')
            self.allowed_values = allowed_values[:self.MAX_ALLOWED_VALUES_COUNT]
        else:
            self.allowed_values = None

        self.min_value = min_value
        self.max_value = max_value
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            unit=unit,
        )

    @abstractmethod
    def _get_validator(self) -> Validator:
        pass

    def to_json(self) -> ParamSpecDict:
        json_: ParamSpecDict = super().to_json()

        if self.allowed_values:
            json_["allowed_values"] = self.allowed_values
        if self.min_value:
            json_["min_value"] = self.min_value
        if self.max_value:
            json_["max_value"] = self.max_value

        return json_

    @classmethod
    def get_str_type(cls) -> str:
        pass

    @classmethod
    def load_from_json(cls, json_: Dict[str, Any]) -> "NumericParam":
        param_spec: NumericParam = super().load_from_json(json_)
        param_spec.allowed_values = json_.get("allowed_values")
        param_spec.min_value = json_.get("min_value")
        param_spec.max_value = json_.get("max_value")
        return param_spec


class IntParam(NumericParam[int]):
    """int param"""

    def _get_validator(self) -> Validator:
        return IntValidator(
            allowed_values=self.allowed_values,
            min_value=self.min_value,
            max_value=self.max_value,
        )

    @classmethod
    def get_str_type(cls) -> str:
        return "int"


class FloatParam(NumericParam[float]):
    """float param"""

    def _get_validator(self) -> Validator:
        return FloatValidator(
            allowed_values=self.allowed_values,
            min_value=self.min_value,
            max_value=self.max_value,
        )

    @classmethod
    def get_str_type(cls) -> str:
        return "float"

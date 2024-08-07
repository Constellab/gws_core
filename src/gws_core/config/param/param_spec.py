

from abc import abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from typing_extensions import TypedDict

from gws_core.config.param.param_spec_decorator import param_spec_decorator

from ...core.classes.validator import (BoolValidator, DictValidator,
                                       FloatValidator, IntValidator,
                                       ListValidator, StrValidator)
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .param_types import ParamSpecDTO, ParamSpecVisibilty

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

    #  If present, the value must be in the array
    allowed_values: Optional[List[ParamSpecType]]

    # Measure unit of the value (ex kg)
    unit: Optional[str]

    # additional info specific for the param
    additional_info: Optional[dict]

    PUBLIC_VISIBILITY: ParamSpecVisibilty = "public"
    PROTECTED_VISIBILITY: ParamSpecVisibilty = "protected"
    PRIVATE_VISIBILITY: ParamSpecVisibilty = "private"

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
        allowed_values: Optional[List[ParamSpecType]] = None,
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

        if not hasattr(self, 'additional_info'):
            self.additional_info = {}

        # the param is optional if the default value is set or optional is set to True
        self.optional = default_value is not None or optional
        self._check_visibility(visibility)
        self._check_allowed_values(allowed_values)

        self.default_value = self.validate(default_value)

    def get_default_value(self) -> ParamSpecType:
        return self.default_value

    def to_dto(self) -> ParamSpecDTO:
        return ParamSpecDTO(
            type=self.get_str_type(),
            optional=self.optional,
            visibility=self.visibility,
            additional_info=self.additional_info or {},
            default_value=self.default_value,
            human_name=self.human_name,
            short_description=self.short_description,
            unit=self.unit,
            allowed_values=self.allowed_values,
        )

    def validate(self, value: Any) -> ParamSpecType:
        """
        Validate the value of the param and return the modified value if needed.
        This method is called when the param is set in the config before saving it in the database.
        The returned value must be serializable in json.l
        """
        return value

    def build(self, value: Any) -> Any:
        """
        Method call before the value is used (in task or view) to apply some transformation if needed by the ParamSpec.
        This does not affect the value in the database.
        """
        return value

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

    def _check_allowed_values(self, allowed_values: Optional[List[ParamSpecType]]) -> None:
        if allowed_values is not None:

            if not isinstance(allowed_values, (list, tuple)):
                raise BadRequestException(
                    f"Invalid allowed values '{allowed_values}' in '{self.get_str_type()}' param, it must be an list or a tuple")

            self.allowed_values = allowed_values
        else:
            self.allowed_values = None

    ################################# CLASS METHODS ###############################

    @classmethod
    @abstractmethod
    def get_str_type(cls) -> str:
        pass

    @classmethod
    def empty(cls) -> "ParamSpec":
        return cls()

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO) -> "ParamSpec":
        param_spec = cls.empty()
        param_spec.default_value = spec_dto.default_value
        param_spec.optional = spec_dto.optional
        param_spec.human_name = spec_dto.human_name
        param_spec.short_description = spec_dto.short_description
        param_spec.unit = spec_dto.unit
        param_spec.visibility = spec_dto.visibility
        param_spec.allowed_values = spec_dto.allowed_values
        param_spec.additional_info = spec_dto.additional_info or {}
        return param_spec


class StrParamAdditionalInfo(TypedDict):
    """Additional info for string param"""

    min_length: Optional[int]
    max_length: Optional[int]


@param_spec_decorator()
class StrParam(ParamSpec[str]):
    """String param"""

    additional_info: Optional[StrParamAdditionalInfo]

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

        self.additional_info = {
            "min_length": min_length,
            "max_length": max_length,
        }
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            allowed_values=allowed_values,
            unit=unit,
        )

    def validate(self, value: Any) -> str:
        if value is None:
            return value

        str_validator = StrValidator(
            allowed_values=self.allowed_values,
            min_length=self.additional_info.get("min_length"),
            max_length=self.additional_info.get("max_length"),
        )
        return str_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return 'str'


@param_spec_decorator()
class TextParam(ParamSpec[str]):
    """Text param used for long string (like multi line text)
    If you want a short string param, use the StrParam.
    """

    def __init__(
        self,
        default_value: Optional[str] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
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
        """

        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def validate(self, value: Any) -> str:
        if value is None:
            return value

        str_validator = StrValidator()
        return str_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return 'text'


@param_spec_decorator()
class BoolParam(ParamSpec[bool]):
    """Boolean param"""

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = False,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None,
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
        """

        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            allowed_values=None,
            unit=None,
        )

    def validate(self, value: Any) -> bool:
        if value is None:
            return value

        bool_validator = BoolValidator()
        return bool_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return 'bool'


@param_spec_decorator()
class DictParam(ParamSpec[dict]):
    """Any json dict param"""

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None
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
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            allowed_values=None,
            unit=None,
        )

    def validate(self, value: Any) -> dict:
        if value is None:
            return value

        dict_validator = DictValidator()
        return dict_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return 'dict'


@param_spec_decorator()
class ListParam(ParamSpec[list]):
    """Any list param"""

    def __init__(
        self,
        default_value: Optional[ParamSpecType] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = None,
        short_description: Optional[str] = None
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
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            allowed_values=None,
            unit=None,
        )

    def validate(self, value: Any) -> list:
        if value is None:
            return value

        list_validator = ListValidator()
        return list_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return 'list'


class NumericParamAdditionalInfo(TypedDict):
    """Additional info for string param"""

    # The minimum value allowed (including)
    min_value: Optional[float]

    # The maximum value allowed (including)
    max_value: Optional[float]


class NumericParam(ParamSpec[ParamSpecType], Generic[ParamSpecType]):
    """Abstract numerci param class (int or float)"""

    additional_info: Optional[NumericParamAdditionalInfo]

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
        self.additional_info = {
            "min_value": min_value,
            "max_value": max_value,
        }
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
            allowed_values=allowed_values,
            unit=unit,
        )

    @classmethod
    @abstractmethod
    def get_str_type(cls) -> str:
        pass


@param_spec_decorator()
class IntParam(NumericParam[int]):
    """int param"""

    def validate(self, value: Any) -> int:
        if value is None:
            return value

        int_validator = IntValidator(
            allowed_values=self.allowed_values,
            min_value=self.additional_info.get("min_value"),
            max_value=self.additional_info.get("max_value"),
        )
        return int_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return "int"


@param_spec_decorator()
class FloatParam(NumericParam[float]):
    """float param"""

    def validate(self, value: Any) -> float:
        if value is None:
            return value

        float_validator = FloatValidator(
            allowed_values=self.allowed_values,
            min_value=self.additional_info.get("min_value"),
            max_value=self.additional_info.get("max_value"),
        )
        return float_validator.validate(value)

    @classmethod
    def get_str_type(cls) -> str:
        return "float"

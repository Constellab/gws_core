from abc import abstractmethod
from typing import Any

from typing_extensions import TypedDict

from gws_core.config.param.param_spec_decorator import (
    ParamSpecCategory,
    param_spec_decorator,
)

from ...core.classes.validator import (
    BoolValidator,
    DictValidator,
    FloatValidator,
    IntValidator,
    ListValidator,
    StrValidator,
)
from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .param_types import (
    ParamSpecDTO,
    ParamSpecSimpleDTO,
    ParamSpecType,
    ParamSpecTypeInfo,
    ParamSpecVisibilty,
)


class ParamSpec:
    """Main abstract class for the spec of config params"""

    # Default value, if None, and optional is false, the config is mandatory
    # If a value is provided there is no need to set the optional
    # Setting optional to True, allows default None value
    default_value: Any | None
    optional: bool

    # Visibility of the param, see doc on type ParamSpecVisibilty for more info
    visibility: ParamSpecVisibilty

    # Human readable name of the param, showed in the interface
    human_name: str | None

    # Description of the param, showed in the interface
    short_description: str | None

    # additional info specific for the param
    additional_info: dict | None

    PUBLIC_VISIBILITY: ParamSpecVisibilty = "public"
    PROTECTED_VISIBILITY: ParamSpecVisibilty = "protected"
    PRIVATE_VISIBILITY: ParamSpecVisibilty = "private"

    # Category of the param spec, set by the @param_spec_decorator
    __category__: ParamSpecCategory

    # Human-readable label of the param spec, set by the @param_spec_decorator
    __label__: str

    def __init__(
        self,
        default_value: Any | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
        self.visibility = visibility
        self.human_name = human_name
        self.short_description = short_description

        if not hasattr(self, "additional_info"):
            self.additional_info = {}

        # the param is optional if the default value is set or optional is set to True
        self.optional = default_value is not None or optional
        self._check_visibility(visibility)

        self.default_value = self.validate(default_value)

    def get_default_value(self) -> Any:
        return self.default_value

    @property
    def accepts_user_input(self) -> bool:
        """Whether this param expects a value supplied by the user.

        False means the value is determined by the system (currently: ComputedParam).
        Consumers should skip such entries when prompting users, when running
        mandatory-field checks, and when validating user-submitted input.
        """
        return True

    def to_dto(self) -> ParamSpecDTO:
        return ParamSpecDTO(
            type=self.get_param_spec_type(),
            optional=self.optional,
            visibility=self.visibility,
            additional_info=self.additional_info or {},
            default_value=self.get_default_value(),
            human_name=self.human_name,
            short_description=self.short_description,
            accepts_user_input=self.accepts_user_input,
        )

    def to_simple_dto(self) -> ParamSpecSimpleDTO:
        return ParamSpecSimpleDTO(
            type=self.get_param_spec_type(),
            optional=self.optional,
            visibility=self.visibility,
            additional_info=self.additional_info or {},
            default_value=self.get_default_value(),
            accepts_user_input=self.accepts_user_input,
        )

    def validate(self, value: Any) -> Any:
        """
        Validate the value of the param and return the modified value if needed.
        This method is called when the param is set in the config before saving it in the database.
        The returned value must be serializable in json.
        """
        return value

    def build(self, value: Any) -> Any:
        """
        Method call before the value is used (in task or view) to apply some transformation if needed by the ParamSpec.
        This does not affect the value in the database.
        """
        return value

    def _check_visibility(self, visibility: ParamSpecVisibilty) -> None:
        allowed_visibility: list[ParamSpecVisibilty] = [
            "public",
            "protected",
            "private",
        ]
        if visibility not in allowed_visibility:
            raise BadRequestException(
                f"The visibilty '{visibility}' of the '{self.get_param_spec_type()}' param is incorrect. It must be one of the following values : {str(allowed_visibility)}"
            )

        # If the visibility is not public, the param must have a default value
        if self.visibility != "public" and not self.optional:
            raise BadRequestException(
                f"The '{self.get_param_spec_type()}' param visibility is set to {self.visibility} but the param is mandatory. It must have a default value of be optional if the visiblity is not public"
            )

    ################################# CLASS METHODS ###############################

    @classmethod
    @abstractmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        pass

    @classmethod
    def empty(cls) -> "ParamSpec":
        return cls()

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> "ParamSpec":
        param_spec = cls.empty()
        param_spec.default_value = spec_dto.default_value
        param_spec.optional = spec_dto.optional
        param_spec.human_name = spec_dto.human_name
        param_spec.short_description = spec_dto.short_description
        param_spec.visibility = spec_dto.visibility
        param_spec.additional_info = spec_dto.additional_info or {}
        if validate and param_spec.default_value is not None:
            try:
                param_spec.validate(param_spec.default_value)
            except Exception as err:
                raise BadRequestException(
                    f"Invalid default value for field '{param_spec.human_name}': {err}"
                ) from err
        return param_spec

    @classmethod
    @abstractmethod
    def get_default_value_param_spec(cls) -> "ParamSpec":
        pass

    @classmethod
    @abstractmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        pass

    @classmethod
    def to_param_spec_info_specs(cls) -> ParamSpecTypeInfo:
        return ParamSpecTypeInfo(
            type=cls.get_param_spec_type(),
            label=cls.__label__,
            category=cls.__category__,
            additional_info=cls.get_additional_infos(),
        )


class StrParamAdditionalInfo(TypedDict):
    """Additional info for string param"""

    min_length: int | None
    max_length: int | None
    allowed_values: list[str] | None


@param_spec_decorator(label="Short text")
class StrParam(ParamSpec):
    """String param"""

    additional_info: StrParamAdditionalInfo

    def __init__(
        self,
        default_value: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
        allowed_values: list[str] | None = None,
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
        """

        self.additional_info = {
            "min_length": min_length,
            "max_length": max_length,
            "allowed_values": allowed_values,
        }
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

        str_validator = StrValidator(
            allowed_values=self.additional_info.get("allowed_values"),
            min_length=self.additional_info.get("min_length"),
            max_length=self.additional_info.get("max_length"),
        )
        return str_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.STRING

    @classmethod
    def get_default_value_param_spec(cls) -> "StrParam":
        return StrParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return {
            "min_length": IntParam(optional=True, human_name="Min length").to_dto(),
            "max_length": IntParam(optional=True, human_name="Max length").to_dto(),
            "allowed_values": ListParam(optional=True, human_name="Allowed values").to_dto(),
        }

    def _check_allowed_values(self, allowed_values: list[str] | None) -> None:
        if allowed_values is not None:
            if not isinstance(allowed_values, (list, tuple)):
                raise BadRequestException(
                    f"Invalid allowed values '{allowed_values}' in 'str' param, it must be an list or a tuple"
                )

            if self.additional_info is not None and self.additional_info["allowed_values"] is None:
                raise BadRequestException("Allowed values are not allowed in the 'str' param")
            self.additional_info["allowed_values"] = allowed_values
        else:
            self.additional_info["allowed_values"] = None


@param_spec_decorator(label="Long text")
class TextParam(ParamSpec):
    """Text param used for long string (like multi line text)
    If you want a short string param, use the StrParam.
    """

    def __init__(
        self,
        default_value: str | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.TEXT

    @classmethod
    def get_default_value_param_spec(cls) -> "TextParam":
        return TextParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None


@param_spec_decorator(label="Boolean")
class BoolParam(ParamSpec):
    """Boolean param"""

    def __init__(
        self,
        default_value: Any | None = False,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
        )

    def validate(self, value: Any) -> bool:
        if value is None:
            return value

        bool_validator = BoolValidator()
        return bool_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.BOOL

    @classmethod
    def get_default_value_param_spec(cls) -> "BoolParam":
        return BoolParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None


@param_spec_decorator(label="Dictionary")
class DictParam(ParamSpec):
    """Any json dict param"""

    def __init__(
        self,
        default_value: Any | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
        )

    def validate(self, value: Any) -> dict:
        if value is None:
            return value

        dict_validator = DictValidator()
        return dict_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.DICT

    @classmethod
    def get_default_value_param_spec(cls) -> "DictParam":
        return DictParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None


@param_spec_decorator(label="List")
class ListParam(ParamSpec):
    """Any list param"""

    def __init__(
        self,
        default_value: Any | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
        )

    def validate(self, value: Any) -> list:
        if value is None:
            return value

        list_validator = ListValidator()
        return list_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.LIST

    @classmethod
    def get_default_value_param_spec(cls) -> "ListParam":
        return ListParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None


class NumericParamAdditionalInfo(TypedDict):
    """Additional info for string param"""

    # The minimum value allowed (including)
    min_value: float | None

    # The maximum value allowed (including)
    max_value: float | None

    # List of allowed values
    allowed_values: list[Any] | None


class NumericParam(ParamSpec):
    """Abstract numerci param class (int or float)"""

    additional_info: NumericParamAdditionalInfo

    def __init__(
        self,
        default_value: Any | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
        allowed_values: list[Any] | None = None,
        min_value: Any | None = None,
        max_value: Any | None = None,
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
        """
        self.additional_info = {
            "min_value": min_value,
            "max_value": max_value,
            "allowed_values": allowed_values,
        }
        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @classmethod
    @abstractmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        pass

    def _check_allowed_values(self, allowed_values: list[Any] | None) -> None:
        if allowed_values is not None:
            if not isinstance(allowed_values, (list, tuple)):
                raise BadRequestException(
                    f"Invalid allowed values '{allowed_values}' in '{self.get_param_spec_type()}' param, it must be an list or a tuple"
                )

            if self.additional_info is not None and self.additional_info["allowed_values"] is None:
                raise BadRequestException(
                    f"Allowed values are not allowed in the '{self.get_param_spec_type()}' param"
                )
            self.additional_info["allowed_values"] = allowed_values
        else:
            self.additional_info["allowed_values"] = None


@param_spec_decorator(label="Integer")
class IntParam(NumericParam):
    """int param"""

    def validate(self, value: Any) -> int:
        if value is None:
            return value

        int_validator = IntValidator(
            allowed_values=self.additional_info.get("allowed_values"),
            min_value=self.additional_info.get("min_value"),
            max_value=self.additional_info.get("max_value"),
        )
        return int_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.INT

    @classmethod
    def get_default_value_param_spec(cls) -> "IntParam":
        return IntParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return {
            "min_value": IntParam(optional=True, human_name="Min value").to_dto(),
            "max_value": IntParam(optional=True, human_name="Max value").to_dto(),
            "allowed_values": ListParam(optional=True, human_name="Allowed values").to_dto(),
        }


@param_spec_decorator(label="Float")
class FloatParam(NumericParam):
    """float param"""

    def validate(self, value: Any) -> float:
        if value is None:
            return value

        float_validator = FloatValidator(
            allowed_values=self.additional_info.get("allowed_values"),
            min_value=self.additional_info.get("min_value"),
            max_value=self.additional_info.get("max_value"),
        )
        return float_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.FLOAT

    @classmethod
    def get_default_value_param_spec(cls) -> "FloatParam":
        return FloatParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return {
            "min_value": FloatParam(optional=True, human_name="Min value").to_dto(),
            "max_value": FloatParam(optional=True, human_name="Max value").to_dto(),
            "allowed_values": ListParam(optional=True, human_name="Allowed values").to_dto(),
        }

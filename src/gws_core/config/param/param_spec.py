import re
import sys
import warnings
from abc import abstractmethod
from typing import Any

from typing_extensions import Self, TypedDict

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
    ParamSpecAiDescriptionDTO,
    ParamSpecDTO,
    ParamSpecSimpleDTO,
    ParamSpecType,
    ParamSpecVisibilty,
)

# Caller locations already warned about - one DeprecationWarning per code location is enough,
# so that importing modules that still pass `allowed_values` is not noisy.
_ALLOWED_VALUES_WARNED_LOCATIONS: set[tuple[str, int]] = set()


def _warn_allowed_values_deprecated(param_class_name: str) -> None:
    """Emit a (deduped) ``DeprecationWarning`` for the deprecated ``allowed_values`` argument.

    DEPRECATED(gws_core 0.22, remove in 0.24): the ``allowed_values`` argument of
    StrParam/IntParam/FloatParam - use ``SelectParam`` instead.
    """
    caller = sys._getframe(2)  # 0: here, 1: the param __init__, 2: the actual caller
    key = (caller.f_code.co_filename, caller.f_lineno)
    if key in _ALLOWED_VALUES_WARNED_LOCATIONS:
        return
    _ALLOWED_VALUES_WARNED_LOCATIONS.add(key)
    warnings.warn(
        f"'allowed_values' on {param_class_name} is deprecated since gws_core 0.22 "
        "and will be removed in 0.24 - use SelectParam instead.",
        DeprecationWarning,
        stacklevel=3,
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

    # Validity state recorded at construction. __init__ never raises on an
    # invalid default value (a ParamSpec is built during class-body evaluation,
    # before the task/view decorator runs). Instead it records the problem here
    # and ConfigSpecs propagates it, so the task is registered but marked as
    # errored. invalid_reason is None when the spec is valid.
    is_valid: bool
    invalid_reason: str | None

    PUBLIC_VISIBILITY: ParamSpecVisibilty = "public"
    PROTECTED_VISIBILITY: ParamSpecVisibilty = "protected"
    PRIVATE_VISIBILITY: ParamSpecVisibilty = "private"

    # Category of the param spec, set by the @param_spec_decorator
    __category__: ParamSpecCategory

    # Whether this type should be offered to the AI form-builder catalog.
    # Off by default — only the generic, user-authorable field types opt in
    # (see describe_for_ai). Lab-specific / system params stay out.
    ai_catalog_member: bool = False

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

        self.is_valid = True
        self.invalid_reason = None

        # validate() raises on an invalid default; record the problem instead
        # of raising so class-body evaluation can complete. ConfigSpecs reads
        # is_valid and the task is registered but marked as errored.
        try:
            self.default_value = self.validate(default_value)
        except Exception as err:
            self.is_valid = False
            self.invalid_reason = f"Invalid default value: {err}"
            self.default_value = None

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
        )

    def to_simple_dto(self) -> ParamSpecSimpleDTO:
        return ParamSpecSimpleDTO(
            type=self.get_param_spec_type(),
            optional=self.optional,
            visibility=self.visibility,
            additional_info=self.additional_info or {},
            default_value=self.get_default_value(),
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
    def get_category(cls) -> ParamSpecCategory | None:
        """The :class:`ParamSpecCategory` this type was registered with by the
        ``@param_spec_decorator``. None if the class was never decorated."""
        return getattr(cls, "__category__", None)

    @classmethod
    def empty(cls) -> Self:
        return cls()

    @classmethod
    def ai_example_spec(cls) -> "ParamSpec":
        """A representative, valid instance of this type used as the example in
        :meth:`describe_for_ai`. Override to show meaningful constraints
        (e.g. min/max). The default is a bare instance with a human_name."""
        return cls(human_name="Example field")

    @classmethod
    def ai_summary(cls) -> str:
        """One-line description of what this field type is for. Override per type."""
        return f"A '{cls.get_param_spec_type().value}' field."

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        """Maps this type's AI-relevant ``additional_info`` constraint keys to a
        human explanation. Default: none. Override on types that expose
        constraints (min/max, lengths, multiple, ...)."""
        return {}

    @classmethod
    def describe_for_ai(cls, example_key: str = "example_field") -> ParamSpecAiDescriptionDTO:
        """Self-describe this param type for an AI form-builder.

        Returns the type tag, a one-line summary, the meaning of each
        AI-relevant ``additional_info`` key, and a real example spec serialized
        exactly as ``ConfigSpecs.from_json`` expects. Built from
        :meth:`ai_example_spec` / :meth:`ai_summary` / :meth:`ai_additional_info_doc`
        so a type only overrides the small pieces it cares about. Keeping this on
        the type (not in the AI service) means a new param type ships its own
        catalog entry."""
        return ParamSpecAiDescriptionDTO(
            type=cls.get_param_spec_type(),
            summary=cls.ai_summary(),
            additional_info_doc=cls.ai_additional_info_doc(),
            example={example_key: cls.ai_example_spec().to_dto().to_json_dict()},
        )

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> Self:
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


class StrParamAdditionalInfo(TypedDict):
    """Additional info for string param"""

    min_length: int | None
    max_length: int | None
    allowed_values: list[str] | None
    # A regular expression the value must fully match (re.fullmatch)
    regex: str | None
    # Plain-language description of the expected format, shown to the user and
    # used in the validation error message instead of the raw regex
    regex_description: str | None


@param_spec_decorator()
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
        regex: str | None = None,
        regex_description: str | None = None,
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
        :param allowed_values: DEPRECATED(gws_core 0.22, remove in 0.24): use SelectParam instead.
                        If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param regex: A regular expression the value must fully match (uses re.fullmatch, so
                        the whole string must conform; anchor explicitly for a partial match).
                        If set, regex_description is required.
        :type regex: Optional[str]
        :param regex_description: Plain-language description of the expected format. Shown to the
                        user and used in the validation error message instead of the raw regex.
                        Mandatory when regex is set.
        :type regex_description: Optional[str]
        """

        if allowed_values is not None:
            # DEPRECATED(gws_core 0.22, remove in 0.24): allowed_values -> use SelectParam
            _warn_allowed_values_deprecated("StrParam")

        if regex is not None:
            # A regex without a plain-language description is useless to the end user
            # (the error message would show the raw pattern), so require both together.
            if not regex_description:
                raise BadRequestException(
                    "'regex_description' is required when 'regex' is set on StrParam: "
                    "it is the human-readable explanation shown to the user."
                )
            # Fail fast on an invalid pattern (an authoring error) at construction
            # rather than when validate() later builds the StrValidator.
            try:
                re.compile(regex)
            except re.error as err:
                raise BadRequestException(
                    f"The regex '{regex}' is not a valid regular expression: {err}"
                ) from err

        self.additional_info = {
            "min_length": min_length,
            "max_length": max_length,
            "allowed_values": allowed_values,
            "regex": regex,
            "regex_description": regex_description,
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

        # StrValidator checks the user input against the regex (re.fullmatch) when
        # one is set, raising with regex_description in the message on a mismatch.
        str_validator = StrValidator(
            allowed_values=self.additional_info.get("allowed_values"),
            min_length=self.additional_info.get("min_length"),
            max_length=self.additional_info.get("max_length"),
            regex=self.additional_info.get("regex"),
            regex_description=self.additional_info.get("regex_description"),
        )
        return str_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.STRING

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "Free text on a single line (names, codes, short answers)."

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        return {
            "min_length": "Minimum number of characters (inclusive), or null.",
            "max_length": "Maximum number of characters (inclusive), or null.",
            "regex": "A regular expression the value must fully match, or null.",
            "regex_description": "Plain-language description of the expected format, shown to the user, or null.",
        }

    @classmethod
    def ai_example_spec(cls) -> "StrParam":
        return cls(
            human_name="Full name",
            short_description="The person's name",
            min_length=1,
            max_length=120,
        )


@param_spec_decorator()
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

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "Multi-line free text (paragraphs, comments, long answers)."

    @classmethod
    def ai_example_spec(cls) -> "TextParam":
        return cls(human_name="Comments", short_description="Any extra notes", optional=True)


@param_spec_decorator()
class BoolParam(ParamSpec):
    """Boolean param"""

    def __init__(
        self,
        default_value: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
    ) -> None:
        """
        :param default_value: Default value of the param. A BoolParam is always optional;
                        when no value is provided it falls back to the default value (False by default).
        :type default_value: bool
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """

        super().__init__(
            default_value=default_value,
            optional=True,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def validate(self, value: Any) -> bool:
        # A bool is never null: a missing/None value means "unchecked" (False).
        if value is None:
            return False

        bool_validator = BoolValidator()
        return bool_validator.validate(value)

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.BOOL

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "A yes/no (true/false) toggle."

    @classmethod
    def ai_example_spec(cls) -> "BoolParam":
        return cls(human_name="Active", default_value=True)


@param_spec_decorator()
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


@param_spec_decorator()
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
        :param allowed_values: DEPRECATED(gws_core 0.22, remove in 0.24): use SelectParam instead.
                        If present, the param value must be in the array
        :type allowed_values: Optional[List[str]]
        :param min: # The minimum value allowed (including)
        :type min:  Optional[ConfigParamType]
        :param max: # The maximum value allowed (including)
        :type max:  Optional[ConfigParamType]
        """
        if allowed_values is not None:
            # DEPRECATED(gws_core 0.22, remove in 0.24): allowed_values -> use SelectParam
            _warn_allowed_values_deprecated(type(self).__name__)

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

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        return {
            "min_value": "Minimum allowed value (inclusive), or null.",
            "max_value": "Maximum allowed value (inclusive), or null.",
        }


@param_spec_decorator()
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

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "A whole number (counts, quantities, years)."

    @classmethod
    def ai_example_spec(cls) -> "IntParam":
        return cls(
            human_name="Age",
            short_description="Age in years",
            optional=True,
            min_value=0,
            max_value=120,
        )


@param_spec_decorator()
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

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "A decimal number (measurements, rates, amounts)."

    @classmethod
    def ai_example_spec(cls) -> "FloatParam":
        return cls(human_name="Mass", short_description="Mass in grams", min_value=0)

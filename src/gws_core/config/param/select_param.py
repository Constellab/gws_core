from enum import Enum
from typing import Any

from typing_extensions import TypedDict

from gws_core.config.param.param_spec_decorator import param_spec_decorator

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .param_spec import ParamSpec
from .param_types import ParamSpecType, ParamSpecVisibilty


class SelectParamOption(TypedDict):
    """A single choice of a :class:`SelectParam`.

    :param label: Human readable text shown in the interface.
    :param value: Value actually stored / returned for this choice (any json
                  serializable value: str, int, float, ...).
    """

    label: str
    value: Any


class SelectParamAdditionalInfo(TypedDict):
    """Additional info for the select param"""

    # Normalized list of available choices (always stored as a list of
    # SelectParamOption, even when the user passed raw values).
    options: list[SelectParamOption]

    # Whether several choices can be selected at once. When True the param value
    # is a list of the selected ``value``s.
    multiple: bool


@param_spec_decorator()
class SelectParam(ParamSpec):
    """Param restricted to a fixed set of choices, rendered as a select / dropdown
    in the interface.

    This replaces the deprecated ``options`` argument of :class:`StrParam`,
    :class:`IntParam` and :class:`FloatParam`.

    The ``options`` argument accepts three forms:

    - an :class:`~enum.Enum` class: one option per member, the member ``name`` is
      the displayed label and the member ``value`` is stored / returned.
    - a list mixing the two following forms:

      - a raw value (``"a"``, ``1``, ``2.5``, ...): the value is both the stored
        value and the displayed label.
      - a ``{"label": ..., "value": ...}`` dict (a :class:`SelectParamOption`):
        the interface shows ``label`` but ``value`` is stored / returned.

    When ``multiple`` is ``True``, several choices can be selected and the param
    value is a list of the selected ``value``s. In that case, if no
    ``default_value`` is provided, the param defaults to an empty list ``[]`` (and
    is therefore optional).
    """

    additional_info: SelectParamAdditionalInfo

    def __init__(
        self,
        options: type[Enum] | list[Any | SelectParamOption] | tuple[Any | SelectParamOption, ...] | None = None,
        multiple: bool = False,
        default_value: Any | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
    ) -> None:
        """
        :param options: The available choices. Either an Enum class (one option
                        per member) or a list / tuple of raw values /
                        ``{"label": ..., "value": ...}`` dicts.
        :type options: type[Enum] | List[Any | SelectParamOption] | Tuple[Any | SelectParamOption, ...]
        :param multiple: If True, several choices can be selected and the value is
                        a list. Defaults to False.
        :type multiple: bool
        :param default_value: Default value, if None, and optional is false, the config is mandatory.
                        When multiple is True and no default is provided, it defaults to an empty list.
                        An Enum member may be passed, its value is then used. When multiple is True,
                        a list / tuple of Enum members may be passed, each member's value is then used.
        :param optional: See default value
        :type optional: Optional[bool]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """
        self.additional_info = {
            "options": self._normalize_allowed_values(options),
            "multiple": multiple,
        }

        # accept an enum member as default value (or, for a multiple select, a
        # list / tuple of enum members)
        if isinstance(default_value, Enum):
            default_value = default_value.value
        elif multiple and isinstance(default_value, (list, tuple)):
            default_value = [
                item.value if isinstance(item, Enum) else item
                for item in default_value
            ]

        # for a multiple select with no explicit default, default to an empty list
        if multiple and default_value is None:
            default_value = []

        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @staticmethod
    def _normalize_allowed_values(
        options: type[Enum] | list[Any | SelectParamOption] | tuple[Any | SelectParamOption, ...] | None,
    ) -> list[SelectParamOption]:
        if options is None:
            return []

        # an Enum class: one option per member (label = name, value = value)
        if isinstance(options, type) and issubclass(options, Enum):
            return [
                {"label": member.name, "value": member.value} for member in options
            ]

        if not isinstance(options, (list, tuple)):
            raise BadRequestException(
                f"Invalid allowed values '{options}' in 'select' param, it must be a list or a tuple"
            )

        normalized: list[SelectParamOption] = []
        for option in options:
            if isinstance(option, dict):
                if "value" not in option:
                    raise BadRequestException(
                        f"Invalid option '{option}' in 'select' param, it must contain a 'value' key"
                    )
                normalized.append(
                    {
                        "label": option.get("label", str(option["value"])),
                        "value": option["value"],
                    }
                )
            else:
                normalized.append({"label": str(option), "value": option})
        return normalized

    def _get_allowed_raw_values(self) -> list[Any]:
        return [option["value"] for option in self.additional_info.get("options") or []]

    def validate(self, value: Any) -> Any:
        if value is None:
            return value

        options = self._get_allowed_raw_values()

        if self.additional_info.get("multiple"):
            if not isinstance(value, (list, tuple)):
                raise BadRequestException(
                    f"Invalid value '{value}' for 'select' param with multiple choices, it must be a list"
                )
            for item in value:
                if item not in options:
                    raise BadRequestException(
                        f"Invalid value '{item}'. Allowed values are {options}"
                    )
            return list(value)

        if value not in options:
            raise BadRequestException(f"Invalid value '{value}'. Allowed values are {options}")
        return value

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.SELECT

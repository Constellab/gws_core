from datetime import date, datetime
from typing import Any

from typing_extensions import TypedDict

from gws_core.config.param.param_spec_decorator import param_spec_decorator

from ...core.exception.exceptions.bad_request_exception import BadRequestException
from .param_spec import ParamSpec
from .param_types import ParamSpecDTO, ParamSpecType, ParamSpecVisibilty


class DateParamAdditionalInfo(TypedDict):
    """Additional info for the date param.

    ``min_value`` / ``max_value`` are stored as ISO 8601 strings to stay
    JSON-serializable (the DTO is round-tripped through json).
    """

    # When True, the param accepts a full datetime (YYYY-MM-DDTHH:MM:SS).
    # When False, only a date (YYYY-MM-DD) is accepted.
    include_time: bool

    # Minimum allowed value (inclusive), ISO 8601 string or None.
    min_value: str | None

    # Maximum allowed value (inclusive), ISO 8601 string or None.
    max_value: str | None


@param_spec_decorator()
class DateParam(ParamSpec):
    """Param for a date, or a datetime when ``include_time`` is True.

    Values are stored as ISO 8601 strings:

    - ``"2026-05-13"`` when ``include_time`` is False
    - ``"2026-05-13T14:30:00"`` when ``include_time`` is True

    The interface uses ``additional_info.include_time`` to pick between a date
    picker and a datetime picker.

    Accepted input types for ``default_value``, ``min_value``, ``max_value`` and
    values passed to :meth:`validate`:

    - an ISO 8601 string
    - a :class:`datetime.date` or :class:`datetime.datetime` instance
    """

    additional_info: DateParamAdditionalInfo

    def __init__(
        self,
        default_value: str | date | datetime | None = None,
        include_time: bool = False,
        min_value: str | date | datetime | None = None,
        max_value: str | date | datetime | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
    ) -> None:
        """
        :param default_value: Default value, if None, and optional is false, the config is mandatory.
                        Setting optional to True, allows default None value.
        :param include_time: If True, the param accepts a full datetime; otherwise a date only.
        :type include_time: bool
        :param min_value: Minimum allowed value (inclusive).
        :param max_value: Maximum allowed value (inclusive).
        :param optional: See default value.
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info.
        :param human_name: Human readable name of the param, showed in the interface.
        :param short_description: Description of the param, showed in the interface.
        """
        self.additional_info = {
            "include_time": include_time,
            "min_value": self._to_iso_or_none(min_value, include_time, "min_value"),
            "max_value": self._to_iso_or_none(max_value, include_time, "max_value"),
        }
        self._check_min_max_order()

        super().__init__(
            default_value=default_value,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def build(self, value: Any) -> date | datetime | None:
        """Convert the stored ISO 8601 string back to a :class:`datetime.date`
        (or :class:`datetime.datetime` when ``include_time`` is True) before the
        value is used in a task.

        The stored value is unchanged.
        """
        if value is None:
            return None

        # Already a date/datetime instance — nothing to do.
        if isinstance(value, datetime):
            return value if self.additional_info["include_time"] else value.date()
        if isinstance(value, date):
            if self.additional_info["include_time"]:
                return datetime(value.year, value.month, value.day)
            return value

        if self.additional_info["include_time"]:
            return datetime.fromisoformat(value)
        return date.fromisoformat(value)

    def validate(self, value: Any) -> str | None:
        if value is None:
            return value

        iso_value = self._to_iso(value, self.additional_info["include_time"])

        min_value = self.additional_info.get("min_value")
        if min_value is not None and iso_value < min_value:
            raise BadRequestException(
                f"Invalid value '{iso_value}' in 'date' param, it must be greater than or equal to '{min_value}'"
            )

        max_value = self.additional_info.get("max_value")
        if max_value is not None and iso_value > max_value:
            raise BadRequestException(
                f"Invalid value '{iso_value}' in 'date' param, it must be less than or equal to '{max_value}'"
            )

        return iso_value

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.DATE

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return "A calendar date, or a date+time when include_time is true."

    @classmethod
    def ai_additional_info_doc(cls) -> dict[str, str]:
        return {
            "include_time": "When true, a full datetime is accepted; otherwise a date only.",
            "min_value": "Earliest allowed value (inclusive), ISO 8601 string or null.",
            "max_value": "Latest allowed value (inclusive), ISO 8601 string or null.",
        }

    @classmethod
    def ai_example_spec(cls) -> "DateParam":
        return cls(human_name="Collected at", short_description="Collection date", optional=True)

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> "DateParam":
        """Override to re-validate ``min_value`` / ``max_value`` carried in the DTO.

        Strict-write, lenient-read: only re-validate the bounds when ``validate``
        is True. When False (the default, used to load persisted content), copy
        ``additional_info`` verbatim so that a previously-stored malformed bound
        does not block read-modify-write operations like deleting the field.
        """
        param: DateParam = super().load_from_dto(spec_dto, validate=validate)  # type: ignore[assignment]
        if not validate:
            return param

        include_time = bool(param.additional_info.get("include_time"))
        param.additional_info = {
            "include_time": include_time,
            "min_value": cls._to_iso_or_none(
                param.additional_info.get("min_value"), include_time, "min_value"
            ),
            "max_value": cls._to_iso_or_none(
                param.additional_info.get("max_value"), include_time, "max_value"
            ),
        }
        param._check_min_max_order()
        return param

    def _check_min_max_order(self) -> None:
        min_iso = self.additional_info["min_value"]
        max_iso = self.additional_info["max_value"]
        if min_iso is not None and max_iso is not None and min_iso > max_iso:
            raise BadRequestException(
                f"'min_value' ({min_iso}) must be less than or equal to 'max_value' ({max_iso}) in 'date' param"
            )

    @staticmethod
    def _to_iso_or_none(
        value: str | date | datetime | None,
        include_time: bool,
        field_name: str = "value",
    ) -> str | None:
        if value is None:
            return None
        return DateParam._to_iso(value, include_time, field_name)

    @staticmethod
    def _to_iso(value: Any, include_time: bool, field_name: str = "value") -> str:
        """Parse and normalize the value to an ISO 8601 string.

        Lexicographic comparison on ISO 8601 strings is order-preserving, so we
        keep min/max comparisons cheap by storing strings rather than re-parsing.
        """
        if isinstance(value, datetime):
            parsed: date | datetime = value if include_time else value.date()
        elif isinstance(value, date):
            if include_time:
                parsed = datetime(value.year, value.month, value.day)
            else:
                parsed = value
        elif isinstance(value, str):
            try:
                if include_time:
                    parsed = datetime.fromisoformat(value)
                else:
                    # fromisoformat accepts a date-only string and returns a date
                    parsed = date.fromisoformat(value)
            except ValueError as err:
                expected = "YYYY-MM-DDTHH:MM:SS" if include_time else "YYYY-MM-DD"
                raise BadRequestException(
                    f"Invalid '{field_name}' '{value}' in 'date' param, expected ISO 8601 format ({expected})"
                ) from err
        else:
            raise BadRequestException(
                f"Invalid '{field_name}' '{value}' in 'date' param, it must be a string, a date or a datetime"
            )

        return parsed.isoformat()

import re
from json import dumps, loads
from typing import Any

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecType


@param_spec_decorator(category=ParamSpecCategory.CODE_PARAM)
class JsonCodeParam(ParamSpec):
    """Param for json code. It shows a simple json IDE
    in the interface to provide code for json.
    The value of this param is a dict.

    It can also handle comments in the JSON code.
    It supports only single-line comments.
    Valid example:
    {
        // This is a comment
        "key": "value"
    }

    Unvalid example:
    {
        /* This is a comment */
        "key": "value"
    }

    Unvalid example:
    {
        "key": "value" // This is a comment
    }

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.JSON_CODE

    ai_catalog_member = True

    @classmethod
    def ai_summary(cls) -> str:
        return (
            "A JSON document, edited in a JSON IDE. The value is a JSON object or array "
            "(single-line // comments are allowed). Use for structured/nested configuration."
        )

    @classmethod
    def ai_example_spec(cls) -> "JsonCodeParam":
        return cls(
            human_name="Settings",
            short_description="Structured JSON configuration",
            optional=True,
        )

    def validate(self, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            value = dumps(value, indent=4)
        if not isinstance(value, str):
            raise ValueError("Invalid value for JsonCodeParam, expected a string.")
        return value.strip()

    def build(self, value: Any) -> dict | list | None:
        """Validate the json code.

        :param value: The value of the param
        :type value: str
        :return: The validated json code
        :rtype: str
        """
        if not value:
            return None

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                # Remove only standalone single-line comments
                # This regex matches lines that only contain whitespace and a comment
                value = re.sub(r"^\s*//.*$", "", value, flags=re.MULTILINE)

                return loads(value)
            except Exception as e:
                raise ValueError(f"Invalid JSON code: {e}") from e
        raise ValueError("Invalid value for JsonCodeParam, expected a string or a dictionary.")

import re
from json import dumps, loads
from typing import Any, Dict

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr


@param_spec_decorator()
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
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.JSON_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "JsonCodeParam":
        return JsonCodeParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

    def validate(self, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, dict) or isinstance(value, list):
            value = dumps(value, indent=4)
        if not isinstance(value, str):
            raise ValueError("Invalid value for JsonCodeParam, expected a string.")
        return value.strip()

    def build(self, value: Any) -> dict:
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
                raise ValueError(f"Invalid JSON code: {e}")
        raise ValueError("Invalid value for JsonCodeParam, expected a string or a dictionary.")

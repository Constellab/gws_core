

from typing import Dict

from gws_core.config.param.param_spec import TextParam
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr


@param_spec_decorator()
class JsonCodeParam(TextParam):
    """Param for json code. It shows a simple json IDE
      in the interface to provide code for json.
      The value of this param is a string containing the json code
      with each line separated by a newline character (\n).

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

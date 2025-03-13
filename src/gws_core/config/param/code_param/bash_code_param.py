

from gws_core.config.param.param_types import ParamSpecTypeStr
from gws_core.core.classes.validator import StrValidator, Validator

from ..param_spec import TextParam


class BashCodeParam(TextParam):
    """Param for bash code. It shows a simple bash IDE
      in the interface to provide code for bash.
      The value of this param is a string containing the bash code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.BASH_CODE

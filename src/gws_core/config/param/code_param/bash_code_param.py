from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecType

from ..param_spec import TextParam


@param_spec_decorator(label="Bash code", type_=ParamSpecCategory.LAB_SPECIFIC)
class BashCodeParam(TextParam):
    """Param for bash code. It shows a simple bash IDE
      in the interface to provide code for bash.
      The value of this param is a string containing the bash code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.BASH_CODE

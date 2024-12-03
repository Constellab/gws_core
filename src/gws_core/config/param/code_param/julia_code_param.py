

from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)

from ..param_spec import TextParam


@param_spec_decorator(type=ParamaSpecType.LAB_SPECIFIC)
class JuliaCodeParam(TextParam):
    """Param for julia code. It shows a simple julia IDE
      in the interface to provide code for julia.
      The value of this param is a string containing the julia code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "julia_code_param"

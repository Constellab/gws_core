

from gws_core.config.param.param_spec_decorator import param_spec_decorator

from ..param_spec import TextParam


@param_spec_decorator()
class RCodeParam(TextParam):
    """Param for r code. It shows a simple r IDE
      in the interface to provide code for r.
      The value of this param is a string containing the r code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "r_code_param"

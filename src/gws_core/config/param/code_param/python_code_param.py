from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecType

from ..param_spec import TextParam


@param_spec_decorator(label="Python code", type_=ParamSpecCategory.LAB_SPECIFIC)
class PythonCodeParam(TextParam):
    """Param for python code. It shows a simple python IDE
      in the interface to provide code for python.
      The value of this param is a string containing the python code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.PYTHON_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "PythonCodeParam":
        return PythonCodeParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return None

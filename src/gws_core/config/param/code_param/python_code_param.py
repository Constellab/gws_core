

from typing import Dict

from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import ParamSpecDTO

from ..param_spec import TextParam


@param_spec_decorator(type=ParamaSpecType.LAB_SPECIFIC)
class PythonCodeParam(TextParam):
    """Param for python code. It shows a simple python IDE
      in the interface to provide code for python.
      The value of this param is a string containing the python code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "python_code_param"

    @classmethod
    def get_default_value_param_spec(cls) -> "PythonCodeParam":
        return PythonCodeParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

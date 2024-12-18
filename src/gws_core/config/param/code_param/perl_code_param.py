

from typing import Dict

from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import ParamSpecDTO

from ..param_spec import TextParam


@param_spec_decorator(type=ParamaSpecType.LAB_SPECIFIC)
class PerlCodeParam(TextParam):
    """Param for perl code. It shows a simple perl IDE
      in the interface to provide code for perl.
      The value of this param is a string containing the perl code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "perl_code_param"

    @classmethod
    def get_default_value_param_spec(cls) -> "PerlCodeParam":
        return PerlCodeParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None



from typing import Dict

from gws_core.config.param.param_spec_decorator import (ParamSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr

from ..param_spec import TextParam


@param_spec_decorator(type_=ParamSpecType.LAB_SPECIFIC)
class RCodeParam(TextParam):
    """Param for r code. It shows a simple r IDE
      in the interface to provide code for r.
      The value of this param is a string containing the r code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.R_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "RCodeParam":
        return RCodeParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

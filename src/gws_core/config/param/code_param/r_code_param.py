from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecType

from ..param_spec import TextParam


@param_spec_decorator(type_=ParamSpecCategory.LAB_SPECIFIC)
class RCodeParam(TextParam):
    """Param for r code. It shows a simple r IDE
      in the interface to provide code for r.
      The value of this param is a string containing the r code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.R_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "RCodeParam":
        return RCodeParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return None

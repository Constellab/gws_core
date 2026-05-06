from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecType

from ..param_spec import TextParam


@param_spec_decorator(label="Perl code", type_=ParamSpecCategory.LAB_SPECIFIC)
class PerlCodeParam(TextParam):
    """Param for perl code. It shows a simple perl IDE
      in the interface to provide code for perl.
      The value of this param is a string containing the perl code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.PERL_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "PerlCodeParam":
        return PerlCodeParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return None

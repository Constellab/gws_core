

from typing import Dict

from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr

from ..param_spec import TextParam


@param_spec_decorator(type_=ParamaSpecType.LAB_SPECIFIC)
class YamlCodeParam(TextParam):
    """Param for yaml code. It shows a simple yaml IDE
      in the interface to provide code for yaml.
      The value of this param is a string containing the yaml code
      with each line separated by a newline character (\n).

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.YAML_CODE

    @classmethod
    def get_default_value_param_spec(cls) -> "YamlCodeParam":
        return YamlCodeParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

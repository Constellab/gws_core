

from typing import Dict

from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import ParamSpecDTO

from .param_spec import DictParam


@param_spec_decorator(type=ParamaSpecType.LAB_SPECIFIC)
class TagsParam(DictParam):
    """TagsParam. Use to define a param for tags

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    :return: _description_
    :rtype: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "tags_param"

    @classmethod
    def get_default_value_param_spec(cls) -> "TagsParam":
        return TagsParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

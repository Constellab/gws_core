from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecType

from .param_spec import DictParam


@param_spec_decorator(type_=ParamSpecCategory.LAB_SPECIFIC)
class TagsParam(DictParam):
    """TagsParam. Use to define a param for tags

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    :return: _description_
    :rtype: _type_
    """

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.TAGS

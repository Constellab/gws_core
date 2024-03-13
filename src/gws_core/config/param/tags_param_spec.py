

from gws_core.config.param.param_spec_decorator import param_spec_decorator

from .param_spec import DictParam


@param_spec_decorator()
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

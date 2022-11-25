# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.validator import DictValidator, Validator

from .param_spec import ParamSpec


class TagsParam(ParamSpec[dict]):
    """TagsParam. Use to define a param for tags

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    :return: _description_
    :rtype: _type_
    """

    @classmethod
    def get_str_type(cls) -> str:
        return "tags_param"

    def _get_validator(self) -> Validator:
        return DictValidator()

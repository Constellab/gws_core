# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any

from gws_core.config.param.param_spec import DictParam
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.impl.rich_text.rich_text import RichText


@param_spec_decorator()
class RichTextParam(DictParam):

    def build(self, value: Any) -> Any:
        if value is None:
            return None

        return RichText.deserialize(value)

    @classmethod
    def get_str_type(cls) -> str:
        return "rich_text_param"

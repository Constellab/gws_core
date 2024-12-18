

from typing import Any, Dict

from gws_core.config.param.param_spec import DictParam
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO
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

    @classmethod
    def get_default_value_param_spec(cls) -> "RichTextParam":
        return RichTextParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

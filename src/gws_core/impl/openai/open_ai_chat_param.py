from typing import Any, Dict, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecType, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr, ParamSpecVisibilty
from gws_core.core.classes.validator import DictValidator
from gws_core.impl.openai.open_ai_chat import OpenAiChat


@param_spec_decorator(type_=ParamSpecType.LAB_SPECIFIC)
class OpenAiChatParam(ParamSpec):
    """Special param for config that create a chat with open ai similar
    to ChatGPT.

    The value of this param will be a OpenAiChat object.

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    context: Optional[str]

    def __init__(
        self,
        context: Optional[str] = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = "Enter your prompt/message",
        short_description: Optional[str] = None,
    ) -> None:
        """
        :param context: Context of the chat, can also be provided during run
        :type context: str
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """
        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )
        self.context = context

    def validate(self, value: Any) -> Any:
        if value is None:
            return value

        if isinstance(value, OpenAiChat):
            return value.to_json()

        dict_validator = DictValidator()
        return dict_validator.validate(value)

    def build(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, OpenAiChat):
            return value
        return OpenAiChat.from_json(value, system_prompt=self.context)

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.OPEN_AI_CHAT

    @classmethod
    def get_default_value_param_spec(cls) -> "OpenAiChatParam":
        return OpenAiChatParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None

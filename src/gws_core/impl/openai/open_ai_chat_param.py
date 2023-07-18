# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_types import ParamSpecVisibilty
from gws_core.core.classes.validator import DictValidator
from gws_core.impl.openai.open_ai_chat import OpenAiChat


class OpenAiChatParam(ParamSpec[dict]):
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
        return OpenAiChat.from_json(value, context=self.context)

    @classmethod
    def get_str_type(cls) -> str:
        return "open_ai_chat_param"

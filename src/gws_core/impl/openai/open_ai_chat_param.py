# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from gws_core.config.param.param_spec import DictParam
from gws_core.config.param.param_types import ParamSpecVisibilty


class OpenAiChatParam(DictParam):
    """Special param for config that create a chat with open ai similar
    to ChatGPT

    :param ParamSpec: _description_
    :type ParamSpec: _type_
    """

    context: Optional[str]

    def __init__(
        self,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
    ) -> None:
        """
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

    @classmethod
    def get_str_type(cls) -> str:
        return "open_ai_chat_param"

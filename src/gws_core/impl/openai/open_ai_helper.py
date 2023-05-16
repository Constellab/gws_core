# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Literal, TypedDict

import openai

from gws_core.impl.openai.open_ai_chat import OpenAiChat

openai.api_key = "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"


class AiChatMessage(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: str


class OpenAiHelper():

    generate_code_rules = "Don't prompt the method signature.\nGenerate the code between ``` characters."

    @classmethod
    def call_gpt(cls, chat: OpenAiChat) -> OpenAiChat:
        """Call gpt chat, and add the response to the chat object as an assistant message

        :param chat: _description_
        :type chat: OpenAiChat
        :return: _description_
        :rtype: OpenAiChat
        """

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat.export_gpt_messages()
        )

        chat.add_assistant_message(completion.choices[0].message.content)

        return chat

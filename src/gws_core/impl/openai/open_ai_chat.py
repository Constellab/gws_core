

from typing import List, Literal, Optional, cast

from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.open_ai_types import (AiChatMessage, OpenAiChatDict,
                                                OpenAiChatMessage)


class OpenAiChat():
    """Class to manage communication with OpenAI chat api

    :return: _description_
    :rtype: _type_
    """

    _messages: List[AiChatMessage]

    def __init__(self, system_prompt: str = None, messages: List[AiChatMessage] = None):
        self._messages = []
        if messages:
            self._messages.extend(messages)

        if system_prompt:
            self.set_system_prompt(system_prompt)

    def call_gpt(self) -> str:
        response = OpenAiHelper.call_gpt(self.export_gpt_messages())

        self.add_assistant_message(response)

        return response

    def _add_message(self, role: Literal['system', 'user', 'assistant'], content: str):
        self._messages.append(AiChatMessage(role=role, content=content))

    def add_assistant_message(self, content: str) -> None:
        self._add_message('assistant', content)

    def add_user_message(self, content: str) -> None:
        self._add_message('user', content)

    def get_last_assistant_message(self, extract_code: bool) -> Optional[str]:
        for message in reversed(self._messages):
            if message.role == 'assistant':
                response = message.content
                if extract_code:
                    return self.extract_code_from_gpt_response(response)
                else:
                    return response

        return None

    def export_gpt_messages(self) -> List[OpenAiChatMessage]:
        # return messages in the format expected by GPT
        return [{'role': message.role, 'content': message.content} for message in self._messages]

    def get_last_message(self) -> Optional[AiChatMessage]:
        if len(self._messages) == 0:
            return None
        return self._messages[-1]

    def get_messages(self) -> List[AiChatMessage]:
        return self._messages

    def last_message_is_user(self) -> bool:
        last_message = self.get_last_message()
        if not last_message:
            return False

        return last_message.is_user()

    def set_system_prompt(self, system_prompt: str):
        if self.has_system_prompt():
            self._messages[0].content = system_prompt
        else:
            self._messages.insert(0, AiChatMessage(role='system', content=system_prompt))

    def has_system_prompt(self) -> bool:
        return len(self._messages) > 0 and self._messages[0].role == 'system'

    def get_system_prompt(self) -> Optional[str]:
        if self.has_system_prompt():
            return self._messages[0].content
        return None

    def has_messages(self) -> bool:
        return len(self._messages) > 0

    def to_json(self) -> OpenAiChatDict:
        return {
            'messages': [cast(OpenAiChatMessage, message.to_json_dict()) for message in self._messages]
        }

    def reset(self):
        system_prompt = self.get_system_prompt()
        self._messages = []
        if system_prompt:
            self.set_system_prompt(system_prompt)

    @classmethod
    def from_json(cls, json: OpenAiChatDict, system_prompt: str = None) -> 'OpenAiChat':
        return cls(messages=AiChatMessage.from_json_list(json['messages']), system_prompt=system_prompt)

    @classmethod
    def extract_code_from_gpt_response(cls, gpt_response: str) -> str:
        """Extract only the code from the GPT response.

        :param gpt_response: _description_
        :type gpt_response: str
        :return: _description_
        :rtype: str
        """
        generated_prompt = gpt_response \
            .replace("```python", "```") \
            .replace("``` python", "```") \
            .replace("```R", "") \
            .replace("``` R", "")

        if "```" not in generated_prompt:
            raise ValueError("No code block found in the AI response")
        return generated_prompt.split("```")[1].strip()

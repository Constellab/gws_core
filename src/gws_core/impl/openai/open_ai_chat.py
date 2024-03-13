

from typing import List, Literal, Optional

from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.open_ai_types import (AiChatMessage, OpenAiChatDict,
                                                OpenAiChatMessage)


class OpenAiChat():
    """Class to manage communication with OpenAI chat api

    :return: _description_
    :rtype: _type_
    """

    _messages: List[AiChatMessage]

    def __init__(self, context: str = None, messages: List[AiChatMessage] = None):
        self._messages = []
        if messages:
            self._messages.extend(messages)

        if context:
            self.set_context(context)

    def call_gpt(self) -> str:
        response = OpenAiHelper.call_gpt(self.export_gpt_messages())

        self.add_assistant_message(response)

        return response

    def _add_message(self, role: Literal['system', 'user', 'assistant'], content: str):
        self._messages.append({'role': role, 'content': content})

    def add_assistant_message(self, content: str):
        self._add_message('assistant', content)

    def get_last_assistant_message(self, extract_code: bool) -> Optional[str]:
        for message in reversed(self._messages):
            if message['role'] == 'assistant':
                response = message['content']
                if extract_code:
                    return self.extract_code_from_gpt_response(response)
                else:
                    return response

        return None

    def export_gpt_messages(self) -> List[OpenAiChatMessage]:
        # return messages in the format expected by GPT
        return [{'role': message['role'], 'content': message['content']} for message in self._messages]

    def get_last_message(self) -> Optional[AiChatMessage]:
        return self._messages[-1]

    def last_message_is_user(self) -> bool:
        last_message = self.get_last_message()
        if not last_message:
            return False

        return last_message['role'] == 'user'

    def set_context(self, context: str):
        if self.has_context():
            self._messages[0]['content'] = context
        else:
            self._messages.insert(0, {'role': 'system', 'content': context})

    def has_context(self) -> bool:
        return len(self._messages) > 0 and self._messages[0]['role'] == 'system'

    def to_json(self) -> OpenAiChatDict:
        return {
            'messages': self._messages
        }

    @classmethod
    def from_json(cls, json: OpenAiChatDict, context: str = None) -> 'OpenAiChat':
        return cls(messages=json['messages'], context=context)

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
        return generated_prompt.split("```")[1].strip()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, TypedDict

import openai

openai.api_key = "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"


class GPTMessage(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: str


class OpenAiHelper():

    generate_code_rules = "Don't prompt the method signature.\nGenerate the code between ``` characters."

    @classmethod
    def call_gpt(cls, messages: List[GPTMessage], context: str = None) -> str:

        if context:
            messages.insert(0, {'role': 'system', 'content': context})

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        return completion.choices[0].message.content

    @classmethod
    def extract_code_from_gpt_response(cls, gpt_response: str) -> str:
        generated_prompt = gpt_response.replace(
            "```python", "```").replace("```R", "")
        return generated_prompt.split("```")[1].strip()

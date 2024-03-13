

from typing import List, Literal

from typing_extensions import NotRequired, TypedDict


class OpenAiChatMessage(TypedDict):
    """Format of the message for OpenAI chat

    :param TypedDict: _description_
    :type TypedDict: _type_
    """
    role: Literal['system', 'user', 'assistant']
    content: str


class AiChatMessage(OpenAiChatMessage):
    """Overload of OpenAiChatMessage to add custom info (not sent to OpenAI)
    but stored in the chat object
    """
    user_id: NotRequired[str]


class OpenAiChatDict(TypedDict):
    """Format of the chat for OpenAI chat

    :param TypedDict: _description_
    :type TypedDict: _type_
    """
    messages: List[OpenAiChatMessage]



from typing import Literal

import streamlit as st

from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_types import AiChatMessage


class StreamlitOpenAiChat():

    chat: OpenAiChat = None
    key: str = None

    def __init__(self, chat: OpenAiChat, key: str) -> None:
        """Initialize the StreamlitOpenAiChat.

        :param chat: OpenAiChat instance to use
        :type chat: OpenAiChat
        :param key: Unique key for storing the chat in session state
        :type key: str
        :raises ValueError: If chat is None
        """
        if chat is None:
            raise ValueError("Chat can't be None")
        self.chat = chat
        self.key = key

    @staticmethod
    def load_from_session(key: str, system_prompt: str = None) -> 'StreamlitOpenAiChat':
        """Load or create a StreamlitOpenAiChat from session state.

        :param key: Unique key for storing the chat in session state
        :type key: str
        :param system_prompt: Optional system prompt for new chat, defaults to None
        :type system_prompt: str, optional
        :return: StreamlitOpenAiChat instance loaded from session or newly created
        :rtype: StreamlitOpenAiChat
        """
        chat: OpenAiChat
        if key in st.session_state:
            chat = st.session_state.get(key)
        else:
            chat = OpenAiChat(system_prompt)

        return StreamlitOpenAiChat(chat, key)

    def show_chat(self) -> None:
        """Display all chat messages in the Streamlit interface."""

        messages = self.chat.get_messages()

        for message in messages:
            if message.role == 'system':
                self._show_system_message(message.content)
            else:
                message_type: Literal['human', 'ai'] = 'human' if message.role == 'user' else 'ai'

                self._show_message(message, message_type)

    def get_last_message(self) -> AiChatMessage:
        """Get the last message in the chat history.

        :return: The last message in the chat
        :rtype: AiChatMessage
        """
        return self.chat.get_last_message()

    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat and save to session state.

        :param message: The user message content
        :type message: str
        """
        self.chat.add_user_message(message)
        self.save()

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the chat and save to session state.

        :param message: The assistant message content
        :type message: str
        """
        self.chat.add_assistant_message(message)
        self.save()

    def last_message_is_user(self) -> bool:
        """Check if the last message in the chat is from the user.

        :return: True if the last message is from the user, False otherwise
        :rtype: bool
        """
        return self.chat.last_message_is_user()

    def has_messages(self) -> bool:
        """Check if the chat has any messages.

        :return: True if the chat has messages, False otherwise
        :rtype: bool
        """
        return self.chat.has_messages()

    def save(self) -> None:
        """Save the current chat state to session state."""
        st.session_state[self.key] = self.chat

    def call_gpt(self) -> str:
        """Call GPT with the current chat history and save the response.

        :return: The GPT response
        :rtype: str
        """
        response = self.chat.call_gpt()
        self.save()
        return response

    def reset(self) -> None:
        """Reset the chat history and save to session state."""
        self.chat.reset()
        self.save()

    def _show_system_message(self, text: str) -> None:
        with st.chat_message('assistant'):
            with st.expander("See system prompt"):
                st.markdown(text)

    def _show_message(self, message: AiChatMessage, type_: Literal['human', 'ai']) -> None:
        with st.chat_message(type_):

            # write dataframes
            dataframes = message.get_dataframes()
            if dataframes:
                for dataframe in dataframes:
                    st.dataframe(dataframe, width='stretch')

            # write plots
            plots = message.get_plots()
            if plots:
                for plot in plots:
                    st.plotly_chart(plot)

            # otherwise write message
            if not dataframes and not plots:
                st.markdown(message.content)

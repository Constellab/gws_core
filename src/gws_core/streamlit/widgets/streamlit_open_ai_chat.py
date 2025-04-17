

from typing import Literal

import streamlit as st

from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_types import AiChatMessage


class StreamlitOpenAiChat():

    chat: OpenAiChat = None
    key: str = None

    def __init__(self, chat: OpenAiChat, key: str) -> None:
        if chat is None:
            raise ValueError("Chat can't be None")
        self.chat = chat
        self.key = key

    @staticmethod
    def load_from_session(key: str) -> 'StreamlitOpenAiChat':
        chat: OpenAiChat
        if key in st.session_state:
            chat = st.session_state.get(key)
        else:
            chat = OpenAiChat()

        return StreamlitOpenAiChat(chat, key)

    def show_chat(self) -> None:

        messages = self.chat.get_messages()

        for message in messages:
            if message.role == 'system':
                self._show_system_message(message.content)
            else:
                message_type = 'human' if message.role == 'user' else 'ai'

                self._show_message(message, message_type)

    def get_last_message(self) -> AiChatMessage:
        return self.chat.get_last_message()

    def add_user_message(self, message: str) -> None:
        self.chat.add_user_message(message)
        self.save()

    def add_assistant_message(self, message: str) -> None:
        self.chat.add_assistant_message(message)
        self.save()

    def last_message_is_user(self) -> bool:
        return self.chat.last_message_is_user()

    def has_messages(self) -> bool:
        return self.chat.has_messages()

    def save(self) -> None:
        st.session_state[self.key] = self.chat

    def call_gpt(self) -> str:
        """Call GPT with the current chat history"""
        response = self.chat.call_gpt()
        self.save()
        return response

    def reset(self) -> None:
        self.chat = OpenAiChat()
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
                    st.dataframe(dataframe, use_container_width=True)

            # write plots
            plots = message.get_plots()
            if plots:
                for plot in plots:
                    st.plotly_chart(plot)

            # otherwise write message
            if not dataframes and not plots:
                st.markdown(message.content)

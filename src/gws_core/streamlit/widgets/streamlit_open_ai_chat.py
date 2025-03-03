

from typing import Literal

import streamlit as st

from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_types import AiChatMessage


class StreamlitOpenAiChat():

    chat: OpenAiChat = None

    def __init__(self, chat: OpenAiChat) -> None:
        if chat is None:
            raise ValueError("Chat can't be None")
        self.chat = chat

    def show_chat(self) -> None:

        messages = self.chat.get_messages()

        for message in messages:
            if message.role == 'system':
                self._show_system_message(message.content)
            else:
                message_type = 'human' if message.role == 'user' else 'ai'

                self._show_message(message, message_type)

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
                    st.dataframe(dataframe)

            # write plots
            plots = message.get_plots()
            if plots:
                for plot in plots:
                    st.plotly_chart(plot)

            # otherwise write message
            if not dataframes and not plots:
                st.markdown(message.content)


import streamlit as st
from pandas import DataFrame

from gws_core import OpenAiChat, Table
from gws_core.impl.table.transformers.table_smart_transformer import \
    AITableTransformer
from gws_core.streamlit import StreamlitContainer, StreamlitOpenAiChat


@st.fragment
def render_smart_transformer_page(data: DataFrame):
    chat: OpenAiChat

    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("Smart Transformer Page")
    with col2:
        if st.button("New chat", key='new_chat'):
            chat = OpenAiChat()
            st.session_state['chat'] = chat

    if st.session_state.get('chat') is None:
        chat = OpenAiChat()
        st.session_state['chat'] = chat
    else:
        chat = st.session_state['chat']

    with StreamlitContainer.container_centered('chat-container'):

        st.info("This is a chat using OpenAI. You data is not send to OpenAI, only the size of your data is sent.")

        streamlit_ai_chat = StreamlitOpenAiChat(chat)
        streamlit_ai_chat.show_chat()

        if chat.last_message_is_user():
            with st.spinner('Processing...'):
                table = Table(data)
                table_transformer = AITableTransformer(table, chat)
                transformed_table: Table = table_transformer.run()

                last_message = chat.get_last_message()
                last_message.add_dataframe(transformed_table.get_data())

                st.session_state['chat'] = chat

                st.rerun(scope='fragment')

        prompt = st.chat_input("Enter your prompt/message here")

        if prompt:
            # add the message and rerun the app, so the message is shown before call to GPT
            chat.add_user_message(prompt)

            # re-run the app
            st.rerun(scope='fragment')

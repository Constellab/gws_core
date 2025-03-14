
import streamlit as st
from auto_ml_components import select_current_table_with_preview
from auto_ml_state import AutoMlState

from gws_core import Table
from gws_core.impl.table.smart_tasks.table_smart_transformer import \
    AITableTransformer
from gws_core.streamlit import StreamlitContainers, StreamlitOpenAiChat


def render_ai_transform_page():

    with StreamlitContainers.container_centered('chat-container'):
        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('transform_chat')

        col1, col2 = StreamlitContainers.columns_with_fit_content('transform-header', [1, 'fit-content'])
        with col1:
            st.subheader("AI transformer")
        with col2:
            if st.button("New chat", key='new_chat'):
                streamlit_ai_chat.reset()

        if not streamlit_ai_chat.has_messages():
            st.info(
                "This chat allows you to make transformations on your table using AI (like removing columns, filtering, cleaning data, etc). "
                + "This chat is using OpenAI, only the size of the table is sent not the data itself.")

        streamlit_ai_chat.show_chat()

        if streamlit_ai_chat.last_message_is_user():
            with st.spinner('Processing...'):
                current_table = AutoMlState.get_current_table()

                table_transformer = AITableTransformer(current_table.table, streamlit_ai_chat.chat)
                transformed_table: Table = table_transformer.run()

                name = current_table.original_name + " ai transformed"
                AutoMlState.add_table(transformed_table, name, set_current=True,
                                      original_name=current_table.original_name)

                last_message = streamlit_ai_chat.get_last_message()
                last_message.add_dataframe(transformed_table.get_data())

                streamlit_ai_chat.save()

                st.rerun(scope='fragment')

        st.divider()
        select_current_table_with_preview()
        prompt = st.chat_input("Enter your prompt/message here. Ex: Remove column 'A' and 'B'.")

        if prompt:
            # add the message and rerun the app, so the message is shown before call to GPT
            streamlit_ai_chat.add_user_message(prompt)

            # re-run the app
            st.rerun(scope='fragment')

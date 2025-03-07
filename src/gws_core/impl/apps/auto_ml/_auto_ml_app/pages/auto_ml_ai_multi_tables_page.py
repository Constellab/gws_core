
from typing import List

import streamlit as st
from auto_ml_state import AutoMlState, TableInfo

from gws_core.impl.table.table import Table
from gws_core.impl.table.transformers.table_smart_multi_transformer import \
    AIMultiTableTransformer
from gws_core.streamlit import StreamlitContainers, StreamlitOpenAiChat

_MULTI_TABLE_KEY = 'multi-table'


def render_ai_multi_tables_page():
    with StreamlitContainers.container_centered('multi-table-container'):

        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('plot_chat')
        col1, col2 = StreamlitContainers.columns_with_fit_content('multi-table-header', [1, 'fit-content'])
        with col1:
            st.subheader("AI multi table")
        with col2:
            if st.button("New chat", key='new_chat'):
                streamlit_ai_chat.reset()

        if not streamlit_ai_chat.has_messages():
            st.info(
                "This chat allows you to make transformations on multiple tables using AI (like merging, joining, etc). "
                + "This chat is using OpenAI, only the size of the table is sent not the data itself.")
        streamlit_ai_chat.show_chat()

        if streamlit_ai_chat.last_message_is_user():
            with st.spinner('Processing...'):
                table_info: List[TableInfo] = st.session_state.get(_MULTI_TABLE_KEY, [])
                if len(table_info) < 2:
                    st.error("Select at least 2 tables to chat with AI.")
                    return
                tables = [table.table for table in table_info]
                plotly_generator = AIMultiTableTransformer(tables, streamlit_ai_chat.chat)
                result: List[Table] = plotly_generator.run()

                last_message = streamlit_ai_chat.get_last_message()
                for table in result:
                    last_message.add_dataframe(table.get_data())
                    AutoMlState.add_table(table, "AI Multi Table", set_current=True)

                streamlit_ai_chat.save()

                st.rerun(scope='fragment')

        st.divider()

        # Table selection
        selected_tables: List[TableInfo] = st.multiselect(
            "Select tables",
            AutoMlState.get_tables(),
            format_func=str
        )

        # Chat input
        if len(selected_tables) >= 2:

            prompt = st.chat_input(
                "Enter your prompt/message here. Ex: Merge the tables")

            if prompt:

                # retrieve the selected tables
                st.session_state[_MULTI_TABLE_KEY] = selected_tables

                # add the message and rerun the app, so the message is shown before call to GPT
                streamlit_ai_chat.add_user_message(prompt)

                # re-run the app
                st.rerun(scope='fragment')

        else:
            st.info("Select at least 2 tables to chat with AI.")


import streamlit as st
from auto_ml_components import select_current_table_with_preview
from auto_ml_state import AutoMlState

from gws_core import PlotlyResource
from gws_core.impl.table.smart_tasks.table_smart_plotly import \
    AITableGeneratePlotly
from gws_core.streamlit import StreamlitContainers, StreamlitOpenAiChat


@st.fragment
def render_ai_plot_page():

    with StreamlitContainers.container_centered('chat-container'):

        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('plot_chat')
        col1, col2 = StreamlitContainers.columns_with_fit_content('chat-header', [1, 'fit-content'])
        with col1:
            st.subheader("AI plots")
        with col2:
            if st.button("New chat", key='new_chat'):
                streamlit_ai_chat.reset()

        if not streamlit_ai_chat.has_messages():
            st.info("This chat allows you to generate plots using AI. "
                    + "This chat is using OpenAI, only the size of the table is sent not the data itself.")

        streamlit_ai_chat.show_chat()

        if streamlit_ai_chat.last_message_is_user():
            with st.spinner('Processing...'):
                current_table = AutoMlState.get_current_table()
                plotly_generator = AITableGeneratePlotly(current_table.table, streamlit_ai_chat.chat)
                plot: PlotlyResource = plotly_generator.run()

                last_message = streamlit_ai_chat.get_last_message()
                last_message.add_plot(plot.get_figure())

                streamlit_ai_chat.save()

                st.rerun(scope='fragment')

        st.divider()
        select_current_table_with_preview()
        prompt = st.chat_input(
            "Enter your prompt/message here. Ex: Generate a scatter plot with column 'A' as x and column 'B' as y.")

        if prompt:
            # add the message and rerun the app, so the message is shown before call to GPT
            streamlit_ai_chat.add_user_message(prompt)

            # re-run the app
            st.rerun(scope='fragment')

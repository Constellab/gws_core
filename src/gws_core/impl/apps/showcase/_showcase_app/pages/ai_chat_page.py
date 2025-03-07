import streamlit as st

from gws_core import PlotlyResource
from gws_core.impl.plotly.table_smart_plotly import AITableGeneratePlotly
from gws_core.streamlit import StreamlitContainers, StreamlitOpenAiChat
from gws_core.test.data_provider import DataProvider


def render_chat():
    st.title("AI Chat")
    st.info("This page contains a showcase for streamlit chat component.")

    table = DataProvider.get_iris_table()

    with StreamlitContainers.container_centered('chat-container'):
        st.dataframe(table.get_data())

        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('plot_chat')
        if st.button("New chat", key='new_chat'):
            streamlit_ai_chat.reset()

        if not streamlit_ai_chat.has_messages():
            st.info("This chat allows you to generate plots using AI. "
                    + "This chat is using OpenAI, only the size of the table is sent not the data itself.")

        streamlit_ai_chat.show_chat()

        if streamlit_ai_chat.last_message_is_user():
            with st.spinner('Processing...'):
                plotly_generator = AITableGeneratePlotly(table, streamlit_ai_chat.chat)
                plot: PlotlyResource = plotly_generator.run()

                last_message = streamlit_ai_chat.get_last_message()
                last_message.add_plot(plot.get_figure())

                streamlit_ai_chat.save()

                st.rerun()

        st.divider()
        prompt = st.chat_input(
            "Enter your prompt/message here. Ex: Generate a scatter plot with column 'A' as x and column 'B' as y.")

        if prompt:
            # add the message and rerun the app, so the message is shown before call to GPT
            streamlit_ai_chat.add_user_message(prompt)

            # re-run the app
            st.rerun()

    _render_code()


def _render_code():
    st.divider()

    st.code('''
    from gws_core import PlotlyResource
    from gws_core.impl.plotly.table_smart_plotly import AITableGeneratePlotly
    from gws_core.streamlit import StreamlitContainer, StreamlitOpenAiChat

    with StreamlitContainer.container_centered('chat-container'):
        st.dataframe(table.get_data())

        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('plot_chat')
        if st.button("New chat", key='new_chat'):
            streamlit_ai_chat.reset()

        if not streamlit_ai_chat.has_messages():
            st.info("This chat allows you to generate plots using AI. "
                    + "This chat is using OpenAI, only the size of the table is sent not the data itself.")

        streamlit_ai_chat.show_chat()

        if streamlit_ai_chat.last_message_is_user():
            with st.spinner('Processing...'):
                plotly_generator = AITableGeneratePlotly(table, streamlit_ai_chat.chat)
                plot: PlotlyResource = plotly_generator.run()

                last_message = streamlit_ai_chat.get_last_message()
                last_message.add_plot(plot.get_figure())

                streamlit_ai_chat.save()

                st.rerun()

        st.divider()
        prompt = st.chat_input(
            "Enter your prompt/message here. Ex: Generate a scatter plot with column 'A' as x and column 'B' as y.")

        if prompt:
            # add the message and rerun the app, so the message is shown before call to GPT
            streamlit_ai_chat.add_user_message(prompt)

            # re-run the app
            st.rerun()'
    ''')

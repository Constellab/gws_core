import streamlit as st
from gws_core import PlotlyResource
from gws_core.impl.table.smart_tasks.table_smart_plotly import AITableGeneratePlotly
from gws_core.test.data_provider import DataProvider
from gws_streamlit_main import StreamlitContainers, StreamlitOpenAiChat

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_chat():
    table = DataProvider.get_iris_table()

    def page_content():
        _render_ai_chat(table)

    page_layout(
        title="AI Chat",
        description="This page contains a showcase for streamlit chat component.",
        content_function=page_content,
    )


def _render_ai_chat(table):
    def example_demo():
        with StreamlitContainers.container_centered("chat-container"):
            st.dataframe(table.get_data())

            streamlit_ai_chat = StreamlitOpenAiChat.load_from_session(
                "plot_chat", system_prompt="Be polite and helpful."
            )
            if st.button("New chat", key="new_chat"):
                streamlit_ai_chat.reset()

            if not streamlit_ai_chat.has_messages():
                st.info(
                    "This chat allows you to generate plots using AI. "
                    + "This chat is using OpenAI, only the size of the table is sent not the data itself."
                )

            streamlit_ai_chat.show_chat()

            if streamlit_ai_chat.last_message_is_user():
                with st.spinner("Processing..."):
                    plotly_generator = AITableGeneratePlotly(table, streamlit_ai_chat.chat)
                    plot: PlotlyResource = plotly_generator.run()

                    last_message = streamlit_ai_chat.get_last_message()
                    last_message.add_plot(plot.get_figure())

                    streamlit_ai_chat.save()

                    st.rerun()

            st.divider()
            prompt = st.chat_input("Enter your prompt/message here.")

            if prompt:
                # add the message and rerun the app, so the message is shown before call to GPT
                streamlit_ai_chat.add_user_message(prompt)

                # re-run the app
                st.rerun()

    code = """import streamlit as st
from gws_core import PlotlyResource
from gws_core.impl.table.smart_tasks.table_smart_plotly import AITableGeneratePlotly
from gws_streamlit_main import StreamlitContainers, StreamlitOpenAiChat

with StreamlitContainers.container_centered('chat-container'):
    st.dataframe(table.get_data())

    streamlit_ai_chat = StreamlitOpenAiChat.load_from_session('plot_chat', system_prompt="Be polite and helpful.")
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
    prompt = st.chat_input("Enter your prompt/message here.")

    if prompt:
        # add the message and rerun the app, so the message is shown before call to GPT
        streamlit_ai_chat.add_user_message(prompt)

        # re-run the app
        st.rerun()"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="AI Chat",
        description="A chat component using OpenAI to generate plots from natural language prompts. Only the table size is sent, not the data itself.",
        doc_class=StreamlitOpenAiChat,
    )

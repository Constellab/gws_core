import streamlit as st
from gws_streamlit_main import StreamlitContainers, StreamlitHelper, StreamlitOpenAiChat

from gws_core import FileHelper, OpenAiHelper

from ..utils.doc_assistant_utils import DocAssistantUtils


def render_assistant_page(type_: str, default_prompt: str, title: str, info: str):
    with StreamlitContainers.container_centered(type_):
        st.subheader(title)

        # Load chat history for this specific type of documentation
        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session(
            f"{type_}_doc_chat", default_prompt
        )

        # Display header with clear chat button
        col1, col2 = StreamlitContainers.columns_with_fit_content("chat-header", [1, "fit-content"])
        with col1:
            st.info(info)
        with col2:
            if st.button("New chat", key=f"new_{type_}_chat"):
                streamlit_ai_chat.reset()

        streamlit_ai_chat.show_chat()

        st.divider()

        # Generate from audio file
        st.subheader("Generate from audio file")
        file = st.file_uploader(
            "Upload an audio file", type=["mp3", "wav", "flac"], key=f"audio_file_{type_}"
        )

        no_file = file is None
        if st.button("Generate documentation from audio", disabled=no_file):
            text = _transcribe_audio_file(file)
            if text:
                generate_doc_from_text(streamlit_ai_chat, text)

        st.divider()

        # Generate from text
        st.subheader("Generate from text")

        text = st.chat_input("Paste the text to generate the documentation")

        if text:
            generate_doc_from_text(streamlit_ai_chat, text)


def _transcribe_audio_file(file):
    """Transcribe audio file and return the text"""
    file_path = DocAssistantUtils.store_uploaded_file_in_tmp_dir(file)

    text: str = None
    with st.spinner("Transcribing the audio file..."):
        # Call whisper
        text = OpenAiHelper.call_whisper(
            file_path, prompt="Transcribe the audio file in corresponding language"
        )
        FileHelper.delete_dir(file_path)

    if not text:
        st.error("Failed to transcribe the audio file. Please try again.")

    return text


def generate_doc_from_text(streamlit_ai_chat: StreamlitOpenAiChat, text: str):
    streamlit_ai_chat.add_user_message(text)

    response: str = None
    with st.spinner("Generating documentation..."):
        response = streamlit_ai_chat.chat.call_gpt()

    if response:
        st.rerun()

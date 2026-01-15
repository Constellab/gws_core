import json
import os

import streamlit as st
from gws_streamlit_main import StreamlitContainers, StreamlitOpenAiChat

from gws_core import FileHelper, OpenAiHelper

from ..utils.doc_assistant_utils import DocAssistantUtils


def load_prompts(prompts_json_path: str) -> dict:
    """Load prompts from JSON file"""
    if not os.path.exists(prompts_json_path):
        st.error(f"Prompts file not found: {prompts_json_path}")
        return {}

    try:
        with open(prompts_json_path) as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading prompts file: {str(e)}")
        return {}


def render_chat_page(prompts_json_path: str):
    """Render the chat page with prompt selection"""

    with StreamlitContainers.container_centered("chat"):
        st.title("Documentation AI Assistant")

        # Load prompts
        prompts = load_prompts(prompts_json_path)

        if not prompts:
            st.warning("No prompts available. Please add prompts in the Config page.")
            return

        # Prompt selector
        st.subheader("Select a prompt")
        prompt_names = list(prompts.keys())

        # Initialize selected prompt in session state if not exists
        if "selected_prompt_name" not in st.session_state:
            st.session_state.selected_prompt_name = prompt_names[0]

        selected_prompt_name = st.selectbox(
            "Choose a prompt:",
            options=prompt_names,
            index=prompt_names.index(st.session_state.selected_prompt_name)
            if st.session_state.selected_prompt_name in prompt_names
            else 0,
            key="prompt_selector",
        )

        # Update session state
        if selected_prompt_name != st.session_state.selected_prompt_name:
            st.session_state.selected_prompt_name = selected_prompt_name

        selected_prompt = prompts[selected_prompt_name]

        # Display the selected prompt
        with st.expander("View prompt content"):
            st.write(selected_prompt)

        st.divider()

        # Load chat history for this specific prompt
        chat_key = f"chat_{selected_prompt_name.replace(' ', '_').lower()}"
        streamlit_ai_chat = StreamlitOpenAiChat.load_from_session(chat_key, selected_prompt)

        # Display header with clear chat button
        col1, col2 = StreamlitContainers.columns_with_fit_content("chat-header", [1, "fit-content"])
        with col1:
            st.info(f"Chat with: {selected_prompt_name}")
        with col2:
            if st.button("New chat", key="new_chat"):
                streamlit_ai_chat.reset()
                st.rerun()

        streamlit_ai_chat.show_chat()

        st.divider()

        # Generate from audio file
        st.subheader("Generate from audio file")
        file = st.file_uploader(
            "Upload an audio file", type=["mp3", "wav", "flac"], key="audio_file"
        )

        no_file = file is None
        if st.button("Generate documentation from audio", disabled=no_file):
            text = _transcribe_audio_file(file)
            if text:
                _generate_doc_from_text(streamlit_ai_chat, text)

        st.divider()

        # Generate from text
        st.subheader("Generate from text")

        text = st.chat_input("Paste the text to generate the documentation")

        if text:
            _generate_doc_from_text(streamlit_ai_chat, text)


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


def _generate_doc_from_text(streamlit_ai_chat: StreamlitOpenAiChat, text: str):
    """Generate documentation from text using AI"""
    streamlit_ai_chat.add_user_message(text)

    response: str = None
    with st.spinner("Generating documentation..."):
        response = streamlit_ai_chat.chat.call_gpt()

    if response:
        st.rerun()

import streamlit as st

from gws_core import FileHelper, OpenAiChat, OpenAiHelper
from gws_core.streamlit import StreamlitContainers, StreamlitHelper


def render_product_assistant_page(default_prompt: str):

    with StreamlitContainers.container_centered('product'):

        st.subheader('Product documentation assistant')

        st.info('This assistant helps you to generate the product documentation of Constellab.')

        with st.expander('Show prompt'):
            prompt = st.text_area('Prompt', value=default_prompt, height=300)

        if not prompt:
            st.error('Please provide a prompt to generate the documentation.')
            st.stop()

        st.divider()

        result_doc: str = None

        # Generate from audio file
        st.subheader('Generate from audio file')
        file = st.file_uploader("Upload an audio file",
                                type=['mp3', 'wav', 'flac'],
                                key='audio_file')

        no_file = file is None
        if st.button('Generate product documentation from audio', disabled=no_file):
            result_doc = _generate_product_doc(file, prompt)

        st.divider()

        # Generate from text
        st.subheader('Generate from text')

        text = st.text_area('Paste the text to generate the documentation', height=300)

        if st.button('Generate product documentation from text'):
            result_doc = _generate_product_doc(text, prompt)

        if result_doc:
            _show_result(result_doc)


def _generate_product_doc(file, prompt: str) -> str:

    file_path = StreamlitHelper.store_uploaded_file_in_tmp_dir(file)

    doc: str = None
    with st.spinner('Transcribing the audio file...'):
        # Call whisper
        doc = OpenAiHelper.call_whisper(file_path, prompt='Transcribe the audio file in corresponding language')
        FileHelper.delete_dir(file_path)

    if not doc:
        st.error('Failed to transcribe the audio file. Please try again.')
        st.stop()

    return _format_doc(doc, prompt)


def _format_doc(doc: str, prompt: str) -> str:
    with st.spinner('Generating documentation...'):

        chat = OpenAiChat(context=prompt)

        chat.add_user_message(doc)

        doc = chat.call_gpt()

        return doc


@st.dialog('Generated documentation', width='large')
def _show_result(doc: str):
    st.write(doc)

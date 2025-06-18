import streamlit as st

from gws_core import RichText
from gws_core.streamlit import StreamlitContainers, rich_text_editor


def render_rich_text_page():
    st.title('Rich text editor')
    st.info('This page contains a showcase for the rich text editor component.')

    with StreamlitContainers.container_centered('container-center'):
        rich_text = RichText()
        rich_text.add_paragraph('This is a paragraph')
        result = rich_text_editor('Rich text editor', initial_value=rich_text, disabled=False, key='rich-text-editor')

        st.write('Result:')
        st.write(result.to_dto_json_dict())

    st.code("""
from gws_core.streamlit import StreamlitContainers, rich_text_editor
from gws_core import RichText

with StreamlitContainers.container_centered('container-center'):
        rich_text = RichText()
        rich_text.add_paragraph('This is a paragraph')
        result = rich_text_editor('Rich text editor', initial_value=rich_text, disabled=False, key='rich-text-editor')

        st.write('Result:')
        st.write(result.to_dto_json_dict())
""")

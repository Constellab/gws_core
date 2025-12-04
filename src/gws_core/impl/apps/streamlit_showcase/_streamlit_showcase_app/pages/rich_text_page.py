import streamlit as st

from gws_core import RichText
from gws_core.streamlit import StreamlitContainers, rich_text_editor

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_rich_text_page():
    def page_content():
        _render_rich_text_editor()

    page_layout(
        title="Rich Text Editor",
        description="This page contains a showcase for the rich text editor component.",
        content_function=page_content,
    )


def _render_rich_text_editor():
    def example_demo():
        with StreamlitContainers.container_centered("container-center"):
            rich_text = RichText()
            rich_text.add_paragraph("This is a paragraph")
            result = rich_text_editor(
                "Rich text editor", initial_value=rich_text, disabled=False, key="rich-text-editor"
            )

            st.write("Result:")
            st.write(result.to_dto_json_dict())

    code = """import streamlit as st
from gws_core.streamlit import StreamlitContainers, rich_text_editor
from gws_core import RichText

with StreamlitContainers.container_centered('container-center'):
    rich_text = RichText()
    rich_text.add_paragraph('This is a paragraph')
    result = rich_text_editor('Rich text editor', initial_value=rich_text, disabled=False, key='rich-text-editor')

    st.write('Result:')
    st.write(result.to_dto_json_dict())"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Rich Text Editor",
        description="A rich text editor component for creating and editing formatted text.",
        doc_func=rich_text_editor,
    )

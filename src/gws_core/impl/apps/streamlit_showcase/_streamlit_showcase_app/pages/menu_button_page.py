import streamlit as st
from gws_core.streamlit import StreamlitMenuButton, StreamlitMenuButtonItem

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


@st.dialog("Menu button")
def _show(text):
    st.write(text)

    if st.button("Close"):
        st.rerun()


def render_menu_button_page():
    def page_content():
        _render_menu_button()

    page_layout(
        title="Menu Button",
        description="This page contains a showcase for menu button component.",
        content_function=page_content,
    )


def _render_menu_button():
    def example_demo():
        button_menu = StreamlitMenuButton()

        # Basic button
        first_button = StreamlitMenuButtonItem(
            label="Button 1", material_icon="check", on_click=lambda: _show("Button 1 clicked")
        )
        button_menu.add_button_item(first_button)

        # add a with children
        button_with_children = StreamlitMenuButtonItem(label="Button 2")
        child_button_1 = StreamlitMenuButtonItem(
            label="Child 1",
            material_icon="check",
            on_click=lambda: _show("Child 1 clicked"),
            color="primary",
        )
        child_button_2 = StreamlitMenuButtonItem(
            label="Delete",
            material_icon="delete",
            on_click=lambda: _show("Delete clicked"),
            color="warn",
        )
        button_with_children.add_children([child_button_1, child_button_2])
        button_menu.add_button_item(button_with_children)

        # add a disabled button with a divider
        disabled_button = StreamlitMenuButtonItem(
            label="Disabled button", material_icon="check", disabled=True, divider=True
        )
        button_menu.add_button_item(disabled_button)

        button_menu.render()

    code = """import streamlit as st
from gws_core.streamlit import StreamlitMenuButton, StreamlitMenuButtonItem

button_menu = StreamlitMenuButton()

# Basic button
first_button = StreamlitMenuButtonItem(label='Button 1', material_icon='check',
                                       on_click=lambda: st.success('Button 1 clicked'))
button_menu.add_button_item(first_button)

# add a with children
button_with_children = StreamlitMenuButtonItem(label='Button 2')
child_button_1 = StreamlitMenuButtonItem(
    label='Child 1', material_icon='check', on_click=lambda: st.success('Child 1 clicked'),
    color='primary')
child_button_2 = StreamlitMenuButtonItem(
    label='Delete', material_icon='delete', on_click=lambda: st.error('Child 2 clicked'),
    color='warn')
button_with_children.add_children([child_button_1, child_button_2])
button_menu.add_button_item(button_with_children)

# add a disabled button with a divider
disabled_button = StreamlitMenuButtonItem(
    label='Disabled button', material_icon='check', disabled=True, divider=True)
button_menu.add_button_item(disabled_button)

button_menu.render()"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Menu Button",
        description="A menu button with support for children buttons, icons, colors, and dividers.",
        doc_class=StreamlitMenuButton,
    )

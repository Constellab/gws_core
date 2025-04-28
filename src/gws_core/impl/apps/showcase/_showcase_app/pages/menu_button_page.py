
import streamlit as st

from gws_core.streamlit import StreamlitMenuButton, StreamlitMenuButtonItem


@st.dialog('Menu button')
def _show(text):
    st.write(text)

    if st.button('Close'):
        st.rerun()


def render_menu_button_page():

    st.title('Menu boutton')

    button_menu = StreamlitMenuButton()

    # Basic button
    first_button = StreamlitMenuButtonItem(label='Button 1', material_icon='check',
                                           on_click=lambda: _show('Button 1 clicked'))
    button_menu.add_button_item(first_button)

    # add a with children
    button_with_children = StreamlitMenuButtonItem(label='Button 2')
    child_button_1 = StreamlitMenuButtonItem(
        label='Child 1', material_icon='check', on_click=lambda: _show('Child 1 clicked'),
        color='primary')
    child_button_2 = StreamlitMenuButtonItem(
        label='Delete', material_icon='delete', on_click=lambda: _show('Delete clicked'),
        color='warn')
    button_with_children.add_children([child_button_1, child_button_2])
    button_menu.add_button_item(button_with_children)

    # add a disabled button with a divider
    disabled_button = StreamlitMenuButtonItem(
        label='Disabled button', material_icon='check', disabled=True, divider=True)
    button_menu.add_button_item(disabled_button)

    button_menu.render()

    st.code('''

import streamlit as st
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

    button_menu.render()
''')

    st.divider()

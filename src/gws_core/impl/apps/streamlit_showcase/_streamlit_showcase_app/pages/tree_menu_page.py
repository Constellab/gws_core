import streamlit as st

from gws_core.streamlit import StreamlitTreeMenu, StreamlitTreeMenuItem


def render_tree_menu_page():

    st.title('Tree menu')

    col1, col2 = st.columns([1, 3])

    selected_item: StreamlitTreeMenuItem = None
    button_menu = StreamlitTreeMenu()
    # Parent item
    parent_item = StreamlitTreeMenuItem(label='Parent', material_icon='folder',
                                        )
    child_1 = StreamlitTreeMenuItem(
        label='Child 1', material_icon='description')
    child_2 = StreamlitTreeMenuItem(
        label='Child 2', material_icon='description')
    parent_item.add_children([child_1, child_2])
    button_menu.add_item(parent_item)

    second_parent = StreamlitTreeMenuItem(label='Parent 2', material_icon='folder')
    # add a disabled button
    no_link = StreamlitTreeMenuItem(
        label='Disabled link', material_icon='description', disabled=True)
    second_parent.add_child(no_link)
    button_menu.add_item(second_parent)

    button_menu.set_default_selected_item(child_1.key)

    with col1:
        # Render the menu tree
        selected_item = button_menu.render()

    with col2:
        st.info("This is a menu tree with the items 'Child 1' selected by default.")
        if selected_item is not None:
            st.write(f'Selected item: {selected_item.label}')
        else:
            st.write('No item selected')

        if st.button('Select Child 2'):
            # Simulate a change> event by selecting Child 2
            button_menu.set_selected_item(child_2.key)
            st.rerun()  # Rerun the app to reflect the change in selection

    st.code('''
import streamlit as st
from gws_core.streamlit import StreamlitTreeMenu, StreamlitTreeMenuItem

col1, col2 = st.columns([1, 3])

selected_item: StreamlitTreeMenuItem = None
button_menu = StreamlitTreeMenu()
# Parent item
parent_item = StreamlitTreeMenuItem(label='Parent', material_icon='folder',
                                    )
child_1 = StreamlitTreeMenuItem(
    label='Child 1', material_icon='description')
child_2 = StreamlitTreeMenuItem(
    label='Child 2', material_icon='description')
parent_item.add_children([child_1, child_2])
button_menu.add_item(parent_item)

second_parent = StreamlitTreeMenuItem(label='Parent 2', material_icon='folder')
# add a disabled button
no_link = StreamlitTreeMenuItem(
    label='Disabled link', material_icon='description', disabled=True)
second_parent.add_child(no_link)
button_menu.add_item(second_parent)

button_menu.set_default_selected_item(child_1.key)

with col1:
    # Render the menu tree
    selected_item = button_menu.render()

with col2:
    st.info("This is a menu tree with the items 'Child 1' selected by default.")
    if selected_item is not None:
        st.write(f'Selected item: {selected_item.label}')
    else:
        st.write('No item selected')

    if st.button('Select Child 2'):
        # Simulate a change> event by selecting Child 2
        button_menu.set_selected_item(child_2.key)
        st.rerun()  # Rerun the app to reflect the change in selection

''')

    st.divider()


import streamlit as st

from gws_core.streamlit import ResourceSearchInput


def render_resources_page():

    st.title('Resource Page')
    st.info('This page contains a showcase for streamlit component to interact with resources.')

    _render_resource_search_input()


def _render_resource_search_input():
    st.subheader('Resource Search Input')
    st.info('This is a resource search input. It contains multiple search options for resources.')

    resource_search = ResourceSearchInput()
    # show only flagged resources
    resource_search.add_flagged_filter(True)
    selected_resource = resource_search.select(
        placeholder='Search for resource', label='Resource Search Input', key='resource-search')

    if selected_resource:
        st.write(f'Selected resource: {selected_resource.name}')
    else:
        st.write('No resource selected')

    st.code('''
    import streamlit as st
    from gws_core.streamlit import ResourceSearchInput
    resource_search = ResourceSearchInput()
    resource_search.add_flagged_filter(True)
    selected_resource = resource_search.select(
        placeholder='Search for resource', label='Resource Search Input', key='resource-search')

    if selected_resource:
        st.write(f'Selected resource: {selected_resource.name}')
    else:
        st.write('No resource selected')

    ''')

    st.divider()

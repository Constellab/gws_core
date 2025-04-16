
import streamlit as st

from gws_core.streamlit import StreamlitResourceSelect


def render_resources_page():

    st.title('Resources')
    st.info('This page contains a showcase for streamlit component to interact with resources.')

    _render_resource_select()


def _render_resource_select():
    st.subheader('Resource Select')
    st.info('This is a resource search input. It allows the user to search and select a resource. The preview is not enable yet.')

    resource_select = StreamlitResourceSelect()
    selected_resource = resource_select.select_resource(
        placeholder='Search for resource', key="resource-selector", defaut_resource=None)

    if selected_resource:
        st.write(f'Selected resource: {selected_resource.name}')
    else:
        st.write('No resource selected')

    st.code("""
st.subheader('Resource Select')

resource_select = StreamlitResourceSelect()
selected_resource = resource_select.select_resource(
    placeholder='Search for resource', key="resource-selector", defaut_resource=None)

if selected_resource:
    st.write(f'Selected resource: {selected_resource.name}')
else:
    st.write('No resource selected')


    """)

    st.divider()

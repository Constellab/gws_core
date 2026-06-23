import streamlit as st
from gws_streamlit_main import StreamlitResourceSelect

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_resources_page():
    def page_content():
        _render_resource_select()

    page_layout(
        title="Resources",
        description="This page contains a showcase for streamlit component to interact with resources.",
        content_function=page_content,
    )


def _render_resource_select():
    def example_demo():
        # fallback_to_system_user lets the component call the API as the system user when
        # the app runs in PUBLIC access mode (no authenticated user). WARNING: this lets any
        # visitor of the app read and write data lab objects through the API.
        resource_select = StreamlitResourceSelect(fallback_to_system_user=True)
        selected_resource = resource_select.select_resource(
            placeholder="Search for resource", key="resource-selector", default_resource=None
        )

        if selected_resource:
            st.write(f"Selected resource: {selected_resource.name}")
        else:
            st.write("No resource selected")

    code = """import streamlit as st
from gws_streamlit_main import StreamlitResourceSelect

# fallback_to_system_user lets the component call the API as the system user when
# the app runs in PUBLIC access mode (no authenticated user). WARNING: this lets any
# visitor of the app read and write data lab objects through the API.
resource_select = StreamlitResourceSelect(fallback_to_system_user=True)
selected_resource = resource_select.select_resource(
    placeholder='Search for resource', key="resource-selector", defaut_resource=None)

if selected_resource:
    st.write(f'Selected resource: {selected_resource.name}')
else:
    st.write('No resource selected')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Resource Select",
        description="A resource search input that allows the user to search and select a resource. The preview is not enabled yet.",
        doc_class=StreamlitResourceSelect,
    )

from typing import List

import streamlit as st
from datahub_dify_app_state import DatahubDifyAppState

from gws_core.impl.dify.datahub_dify_resource import DatahubDifyResource
from gws_core.impl.s3.s3_server_service import S3ServerService
from gws_core.streamlit import (StreamlitAuthenticateUser, StreamlitContainers,
                                StreamlitResourceSelect)


class PageState:

    SELECTED_RESOURCE_KEY = "selected_resource"
    RESOURCES_TO_SYNC_KEY = "resources_to_sync"

    @classmethod
    def get_selected_resource(cls) -> DatahubDifyResource | None:
        """Get the selected resource from the session state."""
        return st.session_state.get(cls.SELECTED_RESOURCE_KEY)

    @classmethod
    def set_selected_resource(cls, resource: DatahubDifyResource):
        """Set the selected resource in the session state."""
        st.session_state[cls.SELECTED_RESOURCE_KEY] = resource

    @classmethod
    def get_resources_to_sync(cls) -> List[DatahubDifyResource]:
        """Get the resources to sync from the session state."""
        if cls.RESOURCES_TO_SYNC_KEY in st.session_state:
            return st.session_state[cls.RESOURCES_TO_SYNC_KEY]

        service = DatahubDifyAppState.get_datahub_chat_dify_service()
        resources_to_sync = service.get_all_resource_to_sync()

        st.session_state[cls.RESOURCES_TO_SYNC_KEY] = resources_to_sync
        return resources_to_sync

    @classmethod
    def clear_resources_to_sync(cls):
        """Clear the resources to sync in the session state."""
        del st.session_state[cls.RESOURCES_TO_SYNC_KEY]


def render_page():

    st.title("⚙️ Configuration")

    with StreamlitContainers.row_container('all_button_actions', gap='1em'):
        if st.button('Refresh resources', key='refresh_resources'):
            PageState.clear_resources_to_sync()
            st.rerun()
        if st.button("Sync all resources", key='sync_all_resources'):
            _sync_all_resources_dialog()

        if st.button("Unsync all resources", key='unsync_all_resources'):
            _unsync_all_resources_dialog()

    _render_sync_one_resource_section()


def _render_sync_one_resource_section():
    """Render the sync one resource section."""

    st.info("Search and select a resource to view its sync status and send it to Dify.")
    selected_resource = PageState.get_selected_resource()
    selected_resource_id = selected_resource.resource_model.id if selected_resource else None

    resource_select = StreamlitResourceSelect()
    resource_select.add_tag_filter(S3ServerService.BUCKET_TAG_NAME, S3ServerService.FOLDERS_BUCKET_NAME)
    resource_select.include_not_flagged_resources()
    resource_model = resource_select.select_resource()
    # Uncomment for dev purpose
    # resource_model = ResourceModel.get_by_id_and_check('eb69aeda-a0be-4285-867b-b7d969247dee')

    # if the user selected a different resource, update the selected resource
    if resource_model and resource_model.id != selected_resource_id:
        PageState.set_selected_resource(DatahubDifyResource(resource_model))
        st.rerun()

    if selected_resource is None:
        return

    if selected_resource.is_compatible_with_dify() is False:
        st.warning("The resource is not compatible with Dify.")
        return

    if selected_resource.is_synced_with_dify():
        st.write("The resource is already sent to Dify.")
        st.write(f"Dify knowledge base id: {selected_resource.get_dify_knowledge_base_id()}")
        st.write(f"Dify document id: {selected_resource.get_and_check_dify_document_id()}")
        st.write(f"Dify sync date: {selected_resource.get_and_check_dify_sync_date()}")

        with StreamlitContainers.row_container('resource_button_actions', gap='1em'):
            _render_send_to_dify_button(selected_resource, f"resend_{selected_resource_id}")
            if st.button("Delete from Dify"):
                datahub_dify_service = DatahubDifyAppState.get_datahub_knowledge_dify_service()

                with st.spinner("Deleting resource from Dify..."):
                    datahub_dify_service.delete_resource_from_dify(selected_resource)
                    st.rerun()

    else:
        st.write("The resource is not sent to Dify.")
        _render_send_to_dify_button(selected_resource, f"send_first_{selected_resource_id}")


def _render_send_to_dify_button(selected_resource: DatahubDifyResource, key: str):
    """Render the send to Dify button."""
    if st.button("Send to Dify", key=key):
        datahub_dify_service = DatahubDifyAppState.get_datahub_knowledge_dify_service()

        with st.spinner("Sending resource to Dify..."):
            datahub_dify_service.send_resource_to_dify(selected_resource)
            st.rerun()


@st.dialog("Sync all resources")
def _sync_all_resources_dialog():
    datahub_dify_service = DatahubDifyAppState.get_datahub_knowledge_dify_service()
    resources: List[DatahubDifyResource]
    with st.spinner("Retrieving resources to sync..."):
        resources = datahub_dify_service.get_all_resource_to_sync()

    st.write(f"Are you sure you want to sync {len(resources)} resources to Dify ? " +
             "It syncs only the resources that are not synced yet.")

    sync_buttons: bool = False

    with StreamlitContainers.row_container('sync_validation', gap='1em'):
        if st.button("Yes"):
            sync_buttons = True

        if st.button("No"):
            st.rerun()

    if sync_buttons:

        with StreamlitAuthenticateUser():
            my_bar = st.progress(0, text="Syncing resources...")
            for i, resource_model in enumerate(resources):
                datahub_dify_service.send_resource_to_dify(resource_model)
                percent = int((i + 1) / len(resources) * 100)
                my_bar.progress(percent, text=f"Syncing resource {i + 1}/{len(resources)}")

        PageState.clear_resources_to_sync()
        st.rerun()


@st.dialog("Unsync all resources")
def _unsync_all_resources_dialog():
    st.write("Are you sure you want to unsync all resources from Dify?")

    unsync_buttons: bool = False
    with StreamlitContainers.row_container('unsync_validation', gap='1em'):
        if st.button("Yes"):
            unsync_buttons = True

        if st.button("No"):
            st.rerun()

    if unsync_buttons:
        datahub_dify_service = DatahubDifyAppState.get_datahub_knowledge_dify_service()

        synced_resources: List[DatahubDifyResource]
        with st.spinner("Retrieving synced resources..."):
            synced_resources = datahub_dify_service.get_all_synced_resources()

        with StreamlitAuthenticateUser():
            my_bar = st.progress(0, text="Unsyncing resources...")
            for i, resource_model in enumerate(synced_resources):
                datahub_dify_service.delete_resource_from_dify(resource_model)
                percent = int((i + 1) / len(synced_resources) * 100)
                my_bar.progress(percent, text=f"Unsyncing resource {i + 1}/{len(synced_resources)}")

        PageState.clear_resources_to_sync()
        st.rerun()

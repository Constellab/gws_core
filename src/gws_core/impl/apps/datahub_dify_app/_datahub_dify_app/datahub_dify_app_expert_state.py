

import streamlit as st

from gws_core.impl.dify.datahub_dify_resource import DatahubDifyResource
from gws_core.impl.dify.doc_expert_ai_page_state import DocAiExpertPageState
from gws_core.space.space_datahub_service import SpaceDatahubService


@st.cache_data()
def get_document_url(document_id: str) -> str | None:
    # retreive the resource id from the document

    datahub_dify_resource = DatahubDifyResource.from_dify_document_id(document_id)
    if datahub_dify_resource is None:
        return None

    datahub_key = datahub_dify_resource.get_datahub_key()

    return SpaceDatahubService.get_instance().get_object_url_from_filename(datahub_key)


class DatahubDifyAppExpertState(DocAiExpertPageState):
    """
    Datahub Dify App Expert State
    """

    def get_document_url(self, document_id: str) -> str | None:
        # retreive the resource id from the document

        return get_document_url(document_id)

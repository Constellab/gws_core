
import streamlit as st

from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_type import CredentialsDataOther
from gws_core.impl.dify.datahub_dify_service import DatahubDifyService
from gws_core.impl.dify.dify_service import DifyService


class DatahubDifyAppState:
    """Class to manage the state of the app.
    """

    CHAT_CREDENTIALS = "chat_credentials"
    KNOWLEDGE_BASE_CREDENTIALS = "knowledge_base_credentials"
    KNOWLEDGE_BASE_ID = "knowledge_base_id"

    @classmethod
    def init(cls, chat_credentials_name: str, knowledge_base_credentials_name: str,
             knowledge_base_id: str):
        """Initialize the session state variables."""
        cls.set_chat_credentials_name(chat_credentials_name)
        cls.set_knowledge_base_credentials_name(knowledge_base_credentials_name)
        cls.set_knowledge_base_id(knowledge_base_id)

    @classmethod
    def set_chat_credentials_name(cls, chat_credentials_name: str):
        current_credentials: CredentialsDataOther = st.session_state.get(cls.CHAT_CREDENTIALS)
        if current_credentials and current_credentials.meta.name == chat_credentials_name:
            return

        credentials = Credentials.find_by_name_and_check(chat_credentials_name)
        st.session_state[cls.CHAT_CREDENTIALS] = credentials.get_data_object()

    @classmethod
    def get_chat_credentials(cls) -> CredentialsDataOther:
        """Get the chat credentials from the session state."""
        return st.session_state.get(cls.CHAT_CREDENTIALS)

    @classmethod
    def set_knowledge_base_credentials_name(cls, knowledge_base_credentials_name: str):
        current_credentials: CredentialsDataOther = st.session_state.get(cls.KNOWLEDGE_BASE_CREDENTIALS)
        if current_credentials and current_credentials.meta.name == knowledge_base_credentials_name:
            return

        credentials = Credentials.find_by_name_and_check(knowledge_base_credentials_name)
        st.session_state[cls.KNOWLEDGE_BASE_CREDENTIALS] = credentials.get_data_object()

    @classmethod
    def get_knowledge_base_credentials(cls) -> CredentialsDataOther:
        """Get the knowledge base credentials from the session state."""
        return st.session_state.get(cls.KNOWLEDGE_BASE_CREDENTIALS)

    @classmethod
    def set_knowledge_base_id(cls, knowledge_base_id: str):
        """Set the knowledge base id in the session state."""
        st.session_state[cls.KNOWLEDGE_BASE_ID] = knowledge_base_id

    @classmethod
    def get_knowledge_base_id(cls) -> str:
        """Get the knowledge base id from the session state."""
        return st.session_state.get(cls.KNOWLEDGE_BASE_ID)

    @classmethod
    def get_datahub_knowledge_dify_service(cls) -> DatahubDifyService:
        dify_service = DifyService.from_credentials(cls.get_knowledge_base_credentials())
        return DatahubDifyService(dify_service, cls.get_knowledge_base_id())

    @classmethod
    def get_datahub_chat_dify_service(cls) -> DatahubDifyService:
        dify_service = DifyService.from_credentials(cls.get_chat_credentials())
        return DatahubDifyService(dify_service, cls.get_knowledge_base_id())

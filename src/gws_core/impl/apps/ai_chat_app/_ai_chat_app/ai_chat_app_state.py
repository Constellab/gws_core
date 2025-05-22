
import uuid
from typing import List, Literal, Optional

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_type import CredentialsDataOther
from gws_core.impl.dify.dify_class import DifySendMessageSource


class ChatMessage(BaseModelDTO):
    role: Literal['user', 'assistant']
    content: str
    id: str
    sources: Optional[List[DifySendMessageSource]] = None


class AiChatAppState:
    """Class to manage the state of the app.
    """

    CHAT_MESSAGES_KEY = "chat_messages"
    CONVERSATION_ID_KEY = "conversation_id"
    CHAT_CREDENTIALS = "chat_credentials"

    @classmethod
    def init(cls, chat_credentials_name: str):
        """Initialize the session state variables."""
        if cls.CHAT_MESSAGES_KEY not in st.session_state:
            st.session_state[cls.CHAT_MESSAGES_KEY] = []
        cls.set_chat_credentials_name(chat_credentials_name)

    @classmethod
    def get_chat_messages(cls) -> List[ChatMessage]:
        """Get the chat messages history from the session state."""
        if cls.CHAT_MESSAGES_KEY not in st.session_state:
            st.session_state[cls.CHAT_MESSAGES_KEY] = []
        return st.session_state[cls.CHAT_MESSAGES_KEY]

    @classmethod
    def add_chat_message(cls, role: Literal['user', 'assistant'], content: str,
                         sources: Optional[List[DifySendMessageSource]] = None):
        """Add a new message to the chat history."""
        message = ChatMessage(
            role=role,
            content=content,
            id=str(uuid.uuid4()),
            sources=sources
        )
        if cls.CHAT_MESSAGES_KEY not in st.session_state:
            st.session_state[cls.CHAT_MESSAGES_KEY] = []
        st.session_state[cls.CHAT_MESSAGES_KEY].append(message)

    @classmethod
    def clear_chat_messages(cls):
        """Clear the chat history."""
        st.session_state[cls.CHAT_MESSAGES_KEY] = []

    @classmethod
    def set_chat_credentials_name(cls, credentials_name: str):
        current_credentials: CredentialsDataOther = st.session_state.get(cls.CHAT_CREDENTIALS)
        if current_credentials and current_credentials.meta.name == credentials_name:
            return

        credentials = Credentials.find_by_name_and_check(credentials_name)
        st.session_state[cls.CHAT_CREDENTIALS] = credentials.get_data_object()

    @classmethod
    def get_chat_credentials(cls) -> CredentialsDataOther:
        """Get the credentials from the session state."""
        return st.session_state.get(cls.CHAT_CREDENTIALS)

    # Conversation ID state methods
    @classmethod
    def get_conversation_id(cls) -> Optional[str]:
        """Get the current conversation ID."""
        return st.session_state.get(cls.CONVERSATION_ID_KEY)

    @classmethod
    def set_conversation_id(cls, conversation_id: str):
        """Set the conversation ID."""
        st.session_state[cls.CONVERSATION_ID_KEY] = conversation_id

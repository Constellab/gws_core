
import uuid
from typing import List, Literal, Optional

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.apps.datahub_dify_app._datahub_dify_app.datahub_dify_app_state import \
    DatahubDifyAppState
from gws_core.impl.dify.dify_class import (DifySendEndMessageStreamResponse,
                                           DifySendMessageSource,
                                           DifySendMessageStreamResponse)
from gws_core.impl.dify.doc_expert_ai_page_state import (
    DocAiExpertDifyDocument, DocAiExpertPageState)
from gws_core.space.space_service import SpaceService
from gws_core.streamlit import StreamlitContainers, StreamlitState


class ChatMessage(BaseModelDTO):
    role: Literal['user', 'assistant']
    content: str
    id: str
    sources: Optional[List[DifySendMessageSource]] = []


class DataHubDifyAppChatPageState:

    ROOT_FOLDER_IDS_KEY = "root_folder_ids"
    CHAT_MESSAGES_KEY = "chat_messages"
    CONVERSATION_ID_KEY = "conversation_id"

    @classmethod
    def get_root_folder_ids(cls) -> List[str]:
        """Get the root folders from the session state."""
        if cls.ROOT_FOLDER_IDS_KEY in st.session_state:
            return st.session_state[cls.ROOT_FOLDER_IDS_KEY]

        # Get all the user root folders from space
        folders = SpaceService.get_instance().get_all_current_user_root_folders()
        if not folders:
            st.error("The user accessible folders could not be found.")

        # For dev purspose to have folder without the space running
        # folders: List[SpaceFolder] = list(SpaceFolder.get_roots())
        st.session_state[cls.ROOT_FOLDER_IDS_KEY] = [folder.id for folder in folders]
        return st.session_state[cls.ROOT_FOLDER_IDS_KEY]

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

    # Conversation ID state methods
    @classmethod
    def get_conversation_id(cls) -> Optional[str]:
        """Get the current conversation ID."""
        return st.session_state.get(cls.CONVERSATION_ID_KEY)

    @classmethod
    def set_conversation_id(cls, conversation_id: str):
        """Set the conversation ID."""
        st.session_state[cls.CONVERSATION_ID_KEY] = conversation_id

    @classmethod
    def clear_chat(cls):
        """Clear the chat history."""
        st.session_state[cls.CHAT_MESSAGES_KEY] = []
        st.session_state[cls.CONVERSATION_ID_KEY] = None


def render_page():

    with StreamlitContainers.container_centered('chat_page'):
        col1, col2 = StreamlitContainers.columns_with_fit_content(key='header-button', cols=[1, 'fit-content'],
                                                                  vertical_align_items='center')

        with col1:
            st.title("AI Chat")

        with col2:
            if st.button("Clear Chat History", icon=':material/replay:'):
                DataHubDifyAppChatPageState.clear_chat()
                st.rerun()

        # Display chat messages
        for message in DataHubDifyAppChatPageState.get_chat_messages():
            with st.chat_message(message.role):
                st.write(message.content)
                _render_sources(message)

        # Check if last message is from the user and needs a response
        messages = DataHubDifyAppChatPageState.get_chat_messages()
        last_message = messages[-1] if messages else None
        if last_message and last_message.role == "user":
            render_stream_response(last_message.content)

        # Chat input
        if prompt := st.chat_input("Ask something..."):
            # Add user message to chat history
            DataHubDifyAppChatPageState.add_chat_message("user", prompt)
            st.rerun()


def _render_sources(message: ChatMessage):
    # Display sources if available
    if message.sources:
        with st.expander("Sources"):
            # Type source to DifySendMessageSource
            for source in message.sources:
                # check if the article expert page is available
                article_expert_state = DocAiExpertPageState.get_instance()

                col1, col2, col3 = StreamlitContainers.columns_with_fit_content(
                    key=f'source_{message.id}_{source.document_name}_header',
                    cols=[1, 'fit-content', 'fit-content'],
                    vertical_align_items='center')
                with col1:
                    st.markdown(f"📄 **{source.document_name}** (Score: {source.score:.2f})")

                if article_expert_state:
                    with col2:
                        document_url = article_expert_state.get_document_url(source.document_id)
                        if document_url:
                            st.link_button('View document', document_url,
                                           icon=':material/open_in_new:')
                    with col3:
                        # Button to switch to article expert page with the selected document
                        if st.button(
                            f"{article_expert_state.config.page_emoji} Open {article_expert_state.config.page_name}",
                                key=f"open_{message.id}_{source.document_name}"):
                            dify_document = DocAiExpertDifyDocument(
                                id=source.document_id,
                                name=source.document_name,
                                dataset_id=source.dataset_id
                            )
                            # Store selected document in state
                            article_expert_state.select_document_and_navigate(dify_document)


def render_stream_response(user_prompt: str):
    if st.session_state.get("chat_is_streaming", False):
        return
    st.session_state["chat_is_streaming"] = True

    datahub_dify_service = DatahubDifyAppState.get_datahub_chat_dify_service()
    user_folders_ids = DataHubDifyAppChatPageState.get_root_folder_ids()

    # Display assistant response with streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # Stream the response using the DifyService
            end_message_response = None

            # Process the streaming response
            for chunk in datahub_dify_service.send_message_stream(
                user_root_folder_ids=user_folders_ids,
                query=user_prompt,
                conversation_id=DataHubDifyAppChatPageState.get_conversation_id(),
                user=StreamlitState.get_current_user().id,
                inputs={},
            ):
                if isinstance(chunk, DifySendMessageStreamResponse):
                    full_response += chunk.answer
                    response_placeholder.markdown(full_response + "▌")
                elif isinstance(chunk, DifySendEndMessageStreamResponse):
                    # It's the end message response
                    end_message_response = chunk

            # Final response without cursor
            response_placeholder.markdown(full_response)

            # Update conversation ID if returned
            if end_message_response and end_message_response.conversation_id:
                DataHubDifyAppChatPageState.set_conversation_id(end_message_response.conversation_id)

            sources = []
            for source in end_message_response.sources:
                # prevent duplicate sources
                if source.document_id not in [s.document_id for s in sources]:
                    sources.append(source)

            # Add assistant response to chat history
            DataHubDifyAppChatPageState.add_chat_message("assistant", full_response, sources)

            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            return
        finally:
            st.session_state["chat_is_streaming"] = False

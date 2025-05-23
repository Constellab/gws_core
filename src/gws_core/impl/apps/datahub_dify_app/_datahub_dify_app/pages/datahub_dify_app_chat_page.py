import uuid
from typing import List, Literal, Optional

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
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

    root_folder_limit: int = None
    state_key: str = None
    root_folder_ids: List[str] = None
    chat_messages: List[ChatMessage] = None
    conversation_id: Optional[str] = None

    def __init__(self, root_folder_limit: int, key: str):
        """Initialize the state with default values"""
        self.root_folder_limit = root_folder_limit
        self.state_key = key
        self.root_folder_ids = []
        self.chat_messages = []
        self.conversation_id = None

    @classmethod
    def init(cls, root_folder_limit: int, key: str = 'datahub-dify-app-chat-page-state'):
        """
        Initialize the session state for the chat page.
        """
        if key in st.session_state:
            return st.session_state[key]

        state = cls(root_folder_limit, key)
        st.session_state[key] = state
        return state

    def get_root_folder_limit(self) -> int:
        """Get the root folder limit from the state."""
        return self.root_folder_limit

    def get_root_folder_ids(self) -> List[str]:
        """Get the root folders from the state."""
        if not self.root_folder_ids:
            try:
                # Get all the user root folders from space
                folders = SpaceService.get_instance().get_all_current_user_root_folders()
                if not folders:
                    st.error("The user accessible folders could not be found.")

                # For dev purspose to have folder without the space running
                # folders: List[SpaceFolder] = list(SpaceFolder.get_roots())
                self.root_folder_ids = [folder.id for folder in folders]
            except Exception as e:
                Logger.error(f"Error while retrieving user accessible folders: {e}")
                Logger.log_exception_stack_trace(e)
                st.error("Could no retrieve the user accessible folders. Please retry later.")
                st.stop()

        return self.root_folder_ids

    def get_chat_messages(self) -> List[ChatMessage]:
        """Get the chat messages history from the state."""
        return self.chat_messages

    def add_chat_message(self, role: Literal['user', 'assistant'], content: str,
                         sources: Optional[List[DifySendMessageSource]] = None):
        """Add a new message to the chat history."""
        message = ChatMessage(
            role=role,
            content=content,
            id=str(uuid.uuid4()),
            sources=sources or []
        )
        self.chat_messages.append(message)

    def get_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID."""
        return self.conversation_id

    def set_conversation_id(self, conversation_id: str):
        """Set the conversation ID."""
        self.conversation_id = conversation_id

    def clear_chat(self):
        """Clear the chat history."""
        self.chat_messages = []
        self.conversation_id = None


def render_page(chat_state: DataHubDifyAppChatPageState):

    with StreamlitContainers.container_centered('chat_page'):
        col1, col2 = StreamlitContainers.columns_with_fit_content(key='header-button', cols=[1, 'fit-content'],
                                                                  vertical_align_items='center')

        with col1:
            st.title("AI Chat")

        with col2:
            if st.button("Clear Chat History", icon=':material/replay:'):
                chat_state.clear_chat()
                st.rerun()

        # Display chat messages
        for message in chat_state.get_chat_messages():
            with st.chat_message(message.role):
                st.write(message.content)
                _render_sources(message)

        # Check if last message is from the user and needs a response
        messages = chat_state.get_chat_messages()
        last_message = messages[-1] if messages else None
        if last_message and last_message.role == "user":
            render_stream_response(last_message.content, chat_state)

        # Chat input
        if prompt := st.chat_input("Ask something..."):
            # Add user message to chat history
            chat_state.add_chat_message("user", prompt)
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


def render_stream_response(user_prompt: str, chat_state: DataHubDifyAppChatPageState):
    if st.session_state.get("chat_is_streaming", False):
        return
    st.session_state["chat_is_streaming"] = True

    datahub_dify_service = DatahubDifyAppState.get_datahub_chat_dify_service()
    user_folders_ids = chat_state.get_root_folder_ids()

    if len(user_folders_ids) > chat_state.get_root_folder_limit():
        st.warning(
            f"You have access to too many root folders ({len(user_folders_ids)}). Only the first {chat_state.get_root_folder_limit()} folders will be used.")

    user_folders_ids = user_folders_ids[:chat_state.get_root_folder_limit()]
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
                conversation_id=chat_state.get_conversation_id(),
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
                chat_state.set_conversation_id(end_message_response.conversation_id)

            sources = []
            for source in end_message_response.sources:
                # prevent duplicate sources
                if source.document_id not in [s.document_id for s in sources]:
                    sources.append(source)

            # Add assistant response to chat history
            chat_state.add_chat_message("assistant", full_response, sources)

            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            return
        finally:
            st.session_state["chat_is_streaming"] = False

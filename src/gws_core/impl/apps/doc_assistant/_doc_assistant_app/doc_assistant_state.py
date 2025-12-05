from dataclasses import dataclass, field

import streamlit as st


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatHistory:
    messages: list[ChatMessage] = field(default_factory=list)


class DocAssistantState:
    """State class to manage chat history for doc assistant"""

    @staticmethod
    def get_instance():
        if "doc_assistant_state" not in st.session_state:
            st.session_state.doc_assistant_state = DocAssistantState()
        return st.session_state.doc_assistant_state

    def __init__(self):
        # Initialize separate chat histories for product and technical documentation
        self.chat_histories: dict[str, ChatHistory] = {
            "product": ChatHistory(),
            "technical": ChatHistory(),
        }

    def add_message(self, chat_type: str, role: str, content: str):
        """Add a message to the chat history for the specified chat type"""
        if chat_type not in self.chat_histories:
            self.chat_histories[chat_type] = ChatHistory()

        self.chat_histories[chat_type].messages.append(ChatMessage(role=role, content=content))

    def get_messages(self, chat_type: str) -> list[ChatMessage]:
        """Get all messages for the specified chat type"""
        if chat_type not in self.chat_histories:
            self.chat_histories[chat_type] = ChatHistory()

        return self.chat_histories[chat_type].messages

    def clear_chat(self, chat_type: str):
        """Clear all messages for the specified chat type"""
        self.chat_histories[chat_type] = ChatHistory()

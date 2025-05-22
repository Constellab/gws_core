import streamlit as st

from gws_core import (DifySendEndMessageStreamResponse,
                      DifySendMessageStreamResponse, DifyService)
from gws_core.impl.apps.ai_chat_app._ai_chat_app.ai_chat_app_state import \
    AiChatAppState
from gws_core.streamlit import StreamlitContainers


def render_chat_page():
    dify_service = DifyService.from_credentials(AiChatAppState.get_chat_credentials())

    with StreamlitContainers.container_centered('chat_page'):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title("AI Chat")

        with col2:
            if st.button("Clear Chat History"):
                AiChatAppState.clear_chat_state()
                st.rerun()

        # Display chat messages
        for message in AiChatAppState.get_chat_messages():
            with st.chat_message(message.role):
                st.write(message.content)

        # Check if last message is from the user and needs a response
        messages = AiChatAppState.get_chat_messages()
        last_message = messages[-1] if messages else None
        if last_message and last_message.role == "user":
            render_stream_response(dify_service, last_message.content)

        # Chat input
        if prompt := st.chat_input("Ask something..."):
            # Add user message to chat history
            AiChatAppState.add_chat_message("user", prompt)
            st.rerun()


def render_stream_response(dify_service: DifyService, user_prompt: str):
    if st.session_state.get("chat_is_streaming", False):
        return
    st.session_state["chat_is_streaming"] = True

    # Display assistant response with streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # Stream the response using the DifyService
            end_message_response = None

            # Process the streaming response
            for chunk in dify_service.send_message_stream(
                query=user_prompt,
                conversation_id=AiChatAppState.get_conversation_id(),
                user='12346',
                inputs={'access_1': 'two', 'access_2': 'one'},
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
                AiChatAppState.set_conversation_id(end_message_response.conversation_id)

            # Add assistant response to chat history
            AiChatAppState.add_chat_message("assistant", full_response)

            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            return
        finally:
            st.session_state["chat_is_streaming"] = False

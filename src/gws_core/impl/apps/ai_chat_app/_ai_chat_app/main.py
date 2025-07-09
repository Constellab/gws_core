

import importlib

import streamlit as st
from _ai_chat_app.ai_chat_app_state import AiChatAppState
from _ai_chat_app.pages import chat_page

sources: list
params: dict

# Uncomment if you want to hide the Streamlit sidebar toggle and always show the sidebar
# from gws_core.streamlit import StreamlitHelper
# StreamlitHelper.hide_sidebar_toggle()

# Initialize the state
AiChatAppState.init(params.get('chat_credentials_name'))


def _render_chat_page():
    importlib.reload(chat_page)
    chat_page.render_chat_page()


_chat_page = st.Page(_render_chat_page, title='Chat page', url_path='chat-page', icon='💬')
pg = st.navigation([_chat_page])

pg.run()

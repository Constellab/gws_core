
import importlib

import streamlit as st

from gws_core.impl.apps.showcase._showcase_app.pages import (ai_chat_page,
                                                             containers_page,
                                                             dataframes_page,
                                                             processes_page,
                                                             resources_page,
                                                             utils_page)
from gws_core.streamlit import StreamlitHelper

sources: list

StreamlitHelper.hide_sidebar_toggle()


def _render_containers_page():
    # importlib.reload(containers_page)
    containers_page.render_containers_page()


def _render_resources_page():
    # importlib.reload(resources_page)
    resources_page.render_resources_page()


def _render_process_page():
    # importlib.reload(processes_page)
    processes_page.render_processes_page()


def _render_dataframes_page():
    # importlib.reload(dataframes_page)
    dataframes_page.render_dataframes_page()


def _render_ai_chat_page():
    # importlib.reload(ai_chat_page)
    ai_chat_page.render_chat()


def _render_utils_page():
    # importlib.reload(utils_page)
    utils_page.render_utils_page()


_containers_page = st.Page(_render_containers_page, title='Containers', url_path='containers', icon='📦')
_resources_page = st.Page(_render_resources_page, title='Resources', url_path='resources', icon='📁')
_processes_page = st.Page(_render_process_page, title='Processes', url_path='processes', icon='🔄')
_dataframes_page = st.Page(_render_dataframes_page, title='Dataframes', url_path='dataframes', icon='📊')
_ai_chat_page = st.Page(_render_ai_chat_page, title='AI Chat', url_path='ai_chat', icon='✨')
_utils_page = st.Page(_render_utils_page, title='Utils', url_path='utils', icon='🛠️')
pg = st.navigation([_containers_page, _resources_page, _processes_page, _dataframes_page, _ai_chat_page, _utils_page])

pg.run()

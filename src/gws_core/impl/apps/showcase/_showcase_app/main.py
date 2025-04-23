
import importlib

import streamlit as st

from gws_core.impl.apps.showcase._showcase_app.pages import (ai_chat_page,
                                                             containers_page,
                                                             dataframes_page,
                                                             menu_button_page,
                                                             processes_page,
                                                             resources_page,
                                                             rich_text_page,
                                                             utils_page)
from gws_core.streamlit import StreamlitHelper, StreamlitRouter

sources: list

StreamlitHelper.hide_sidebar_toggle()

router = StreamlitRouter.load_from_session()


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


def _render_rich_text_page():
    # importlib.reload(rich_text_page)
    rich_text_page.render_rich_text_page()


def _render_ai_chat_page():
    # importlib.reload(ai_chat_page)
    ai_chat_page.render_chat()


def _render_menu_button_page():
    # importlib.reload(menu_button_page)
    menu_button_page.render_menu_button_page()


def _render_utils_page():
    # importlib.reload(utils_page)
    utils_page.render_utils_page()


router.add_page(_render_containers_page, title='Containers', url_path='containers', icon='📦')
router.add_page(_render_resources_page, title='Resources', url_path='resources', icon='📁')
router.add_page(_render_process_page, title='Processes', url_path='processes', icon='🔄')
router.add_page(_render_dataframes_page, title='Dataframes', url_path='dataframes', icon='📊')
router.add_page(_render_rich_text_page, title='Rich Text', url_path='rich_text', icon='📝')
router.add_page(_render_ai_chat_page, title='AI Chat', url_path='ai_chat', icon='✨')
router.add_page(_render_menu_button_page, title='Menu Button', url_path='menu_button', icon=':material/more_vert:')
router.add_page(_render_utils_page, title='Utils', url_path='utils', icon='🛠️')
router.run()

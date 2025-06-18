import os

import streamlit as st
from gws_core.streamlit import (StreamlitHelper, StreamlitRouter,
                                StreamlitTranslateLang,
                                StreamlitTranslateService)


def render_utils_page():
    st.title('Utils')
    st.info('This page contains a showcase for streamlit utilities.')

    _render_authenticate_user()
    _render_hide_sidebar_toggle()
    _render_toggle_sidebar()
    _render_router()
    _render_translation()


def _render_authenticate_user():
    st.subheader('Authenticate User')
    st.info('By default the user is authenticated if the user is logged in. But in some run context (like a button click), the execution context is different and the user may not be authenticated. This utility allows to force authenticate the user.')
    st.code('''
import streamlit as st
import gws_core.streamlit as StreamlitAuthenticateUser

def render():
    st.write('User is authenticated')
    st.button('Action', on_click=_on_click)


def _on_click():
    st.write('User is not authenticated')
    with StreamlitAuthenticateUser() as user:
        st.write('User is authenticated ' + user.first_name)
''')
    st.divider()


def _render_hide_sidebar_toggle():
    st.subheader('Hide Toolbar Toogle Buttons')
    st.info('This utility allows to hide the sidebar toogle buttons.')
    st.code('''
import gws_core.streamlit as StreamlitHelper'

StreamlitHelper.hide_toolbar()
''')
    st.divider()


def _render_toggle_sidebar():
    st.subheader('Programatically Toggle Sidebar')
    st.info('This utility allows to toggle the sidebar programatically. It uses st.rerun() to refresh the page.')

    if st.button('Toggle Sidebar'):
        StreamlitHelper.toggle_sidebar()

    if st.button('Show sidebar'):
        StreamlitHelper.show_sidebar()

    if st.button('Hide sidebar'):
        StreamlitHelper.hide_sidebar()
    st.code('''
import gws_core.streamlit as StreamlitHelper

if st.button('Toggle Sidebar'):
    StreamlitHelper.toggle_sidebar()

if st.button('Show sidebar'):
    StreamlitHelper.show_sidebar()

if st.button('Hide sidebar'):
    StreamlitHelper.hide_sidebar()
''')
    st.divider()


def _render_router():
    st.subheader('Router')
    st.info('This utility allows to create streamlit pages and navigate between them.')

    router = StreamlitRouter.load_from_session()

    if st.button('Navigate to Containers'):
        router.navigate('containers')

    st.code('''
# Define the pages
from gws_core.streamlit import StreamlitRouter

router = StreamlitRouter.load_from_session()

router.add_page(_render_containers_page_function, title='Containers', url_path='containers', icon='📦')

# Page available but not shown in the sidebar, can only be access with router.navigate()
router.add_page(_render_resources_page_function, title='Resources',
                url_path='resources', icon='📁', hide_from_sidebar=True)

# Navigate to a page
from gws_core.streamlit import StreamlitRouter

router = StreamlitRouter.load_from_session()

if st.button('Navigate to Containers'):
    router.navigate('containers')
''')
    st.divider()


def _render_translation():
    st.subheader('Translation')
    st.info('This utility allows to translate the app in different languages.')

    lang_translation_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'lang')
    translate_service = StreamlitTranslateService(lang_translation_folder_path)

    current_lang = translate_service.get_lang()
    st.write(f"Current language: {current_lang.value}")

    if st.button(translate_service.translate("change_language")):
        if current_lang == StreamlitTranslateLang.EN:
            translate_service.change_lang(StreamlitTranslateLang.FR)
        else:
            translate_service.change_lang(StreamlitTranslateLang.EN)

    st.write(translate_service.translate("test_key"))

    st.code('''
from gws_core.streamlit import StreamlitTranslateLang,
                               StreamlitTranslateService

# Path of the folder containing the translation files that you created ("en.json" and "fr.json" by default)
lang_translation_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'lang')

translate_service = StreamlitTranslateService(lang_translation_folder_path)

# Get the current language (default is English)
current_lang = translate_service.get_lang()

if st.button("Change lang"):
    if current_lang == StreamlitTranslateLang.EN:
        translate_service.change_lang(StreamlitTranslateLang.FR)
    else:
        translate_service.change_lang(StreamlitTranslateLang.EN)

st.write(translate_service.translate("key"))
''')
    st.divider()

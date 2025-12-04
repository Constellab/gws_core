import os

import streamlit as st

from gws_core.streamlit import (
    StreamlitHelper,
    StreamlitRouter,
    StreamlitState,
    StreamlitTranslateLang,
    StreamlitTranslateService,
)

from ..components.example_tabs_component import example_tabs
from ..components.page_layout_component import page_layout


def render_utils_page():
    def page_content():
        _render_authenticate_user()
        _render_streamlit_state()
        _render_hide_sidebar_toggle()
        _render_toggle_sidebar()
        _render_router()
        _render_translation()

    page_layout(
        title="Utils",
        description="This page contains a showcase for streamlit utilities.",
        content_function=page_content,
    )


def _render_authenticate_user():
    code = """import streamlit as st
import gws_core.streamlit as StreamlitAuthenticateUser

def render():
    st.write('User is authenticated')
    st.button('Action', on_click=_on_click)


def _on_click():
    st.write('User is not authenticated')
    with StreamlitAuthenticateUser() as user:
        st.write('User is authenticated ' + user.first_name)"""

    example_tabs(
        code=code,
        title="Authenticate User",
        description="Force authenticate the user in different execution contexts.",
        doc_func=None,
    )


def _render_streamlit_state():
    def example_demo():
        user = StreamlitState.get_current_user()

        if user:
            st.write(f"Current user: {user.first_name} {user.last_name}")
        else:
            st.write("No user connected")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitState

user = StreamlitState.get_current_user()

if user:
    st.write(f"Current user: {user.first_name} {user.last_name}")
else:
    st.write("No user connected")"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Streamlit State",
        description="Access state information like current user.",
        doc_func=StreamlitState.get_current_user,
    )


def _render_hide_sidebar_toggle():
    code = """from gws_core.streamlit import StreamlitHelper

StreamlitHelper.hide_toolbar()"""

    example_tabs(
        code=code,
        title="Hide Toolbar Toggle Buttons",
        description="Hide the sidebar toggle buttons from the toolbar.",
    )


def _render_toggle_sidebar():
    def example_demo():
        if st.button("Toggle Sidebar"):
            StreamlitHelper.toggle_sidebar()

        if st.button("Show sidebar"):
            StreamlitHelper.show_sidebar()

        if st.button("Hide sidebar"):
            StreamlitHelper.hide_sidebar()

    code = """import streamlit as st
from gws_core.streamlit import StreamlitHelper

if st.button('Toggle Sidebar'):
    StreamlitHelper.toggle_sidebar()

if st.button('Show sidebar'):
    StreamlitHelper.show_sidebar()

if st.button('Hide sidebar'):
    StreamlitHelper.hide_sidebar()"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Programmatically Toggle Sidebar",
        description="Toggle the sidebar visibility programmatically.",
        doc_func=StreamlitHelper.toggle_sidebar,
    )


def _render_router():
    def example_demo():
        router = StreamlitRouter.load_from_session()

        if st.button("Navigate to Containers"):
            router.navigate("containers")

    code = """import streamlit as st
from gws_core.streamlit import StreamlitRouter

# Define the pages
router = StreamlitRouter.load_from_session()

router.add_page(_render_containers_page_function, title='Containers', url_path='containers', icon='📦')

# Page available but not shown in the sidebar, can only be access with router.navigate()
router.add_page(_render_resources_page_function, title='Resources',
                url_path='resources', icon='📁', hide_from_sidebar=True)

# Navigate to a page
router = StreamlitRouter.load_from_session()

if st.button('Navigate to Containers'):
    router.navigate('containers')"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Router",
        description="Create streamlit pages and navigate between them.",
        doc_func=StreamlitRouter.navigate,
    )


def _render_translation():
    def example_demo():
        lang_translation_folder_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), os.pardir, "lang"
        )
        translate_service = StreamlitTranslateService(lang_translation_folder_path)

        current_lang = translate_service.get_lang()
        st.write(f"Current language: {current_lang.value}")

        if st.button(translate_service.translate("change_language")):
            if current_lang == StreamlitTranslateLang.EN:
                translate_service.change_lang(StreamlitTranslateLang.FR)
            else:
                translate_service.change_lang(StreamlitTranslateLang.EN)

        st.write(translate_service.translate("test_key"))

    code = """import streamlit as st
import os
from gws_core.streamlit import StreamlitTranslateLang, StreamlitTranslateService

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

st.write(translate_service.translate("key"))"""

    example_tabs(
        example_function=example_demo,
        code=code,
        title="Translation",
        description="Translate the app in different languages.",
        doc_func=StreamlitTranslateService.translate,
    )

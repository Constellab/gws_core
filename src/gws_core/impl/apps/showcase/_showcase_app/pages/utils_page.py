import streamlit as st

from gws_core.streamlit import StreamlitHelper


def render_utils_page():
    st.title('Utils')
    st.info('This page contains a showcase for streamlit utilities.')

    _render_authenticate_user()
    _render_hide_sidebar_toggle()
    _render_toggle_sidebar()


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
    with StreamlitAuthenticateUser():
        st.write('User is authenticated')
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

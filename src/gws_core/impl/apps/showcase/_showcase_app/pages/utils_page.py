import streamlit as st


def render_utils_page():
    st.title('Utils Page')
    st.info('This page contains a showcase for streamlit utilities.')

    _render_authenticate_user()


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

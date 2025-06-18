import streamlit as st
from state import State


def _on_change_value():
    State.set_value(st.session_state.get('first_page_input'))


def render_first_page():

    st.title("First Page")

    st.write("This is the first page of the app.")

    value = st.text_input("Enter a value", value=State.get_value(), on_change=_on_change_value,
                          key="first_page_input")

    st.write(f"Value: {value}")

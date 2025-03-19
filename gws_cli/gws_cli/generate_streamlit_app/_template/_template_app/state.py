
import streamlit as st


class State:
    """Class to manage the state of the app.
    """

    VALUE_KEY = "value"

    @classmethod
    def get_value(cls) -> str:
        return st.session_state.get(cls.VALUE_KEY, 'Default value')

    @classmethod
    def set_value(cls, value: str):
        st.session_state[cls.VALUE_KEY] = value

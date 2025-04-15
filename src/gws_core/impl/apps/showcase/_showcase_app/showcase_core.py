
import streamlit as st


class ShowcaseCore:
    """
    Showcase Core class.
    """

    @classmethod
    def show_requires_authentication_warning(cls):
        st.warning('This component requires user authentication to work. ' +
                   'The `requires_authentication` of the `StreamlitResource` must be set to `True`. ' +
                   'It can\'t be used in a publicly shared app.')

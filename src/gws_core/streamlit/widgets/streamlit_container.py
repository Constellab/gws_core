import streamlit as st

from .streamlit_helper import StreamlitHelper


class StreamlitContainer():

    @classmethod
    def container_centered(cls, key: str, max_width: str = '48em'):
        css_class = StreamlitHelper.get_element_css_class(key)
        st.markdown(
            f"""
            <style>
            .{css_class} {{
                max-width: {max_width};
                margin-inline: auto;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        container = st.container(key=key)
        return container.columns(1)[0]

import os
import re
from typing import Any

import streamlit as st

from gws_core.core.utils.settings import Settings


class StreamlitHelper:
    CSS_PREFIX = "st-key-"
    SIDEBAR_STATE_KEY = "__gws_sidebar_state__"

    @classmethod
    def get_element_css_class(cls, key: str) -> str:
        """Generate a valid CSS class name from the given key.

        Ensures the class name:
        - Contains only alphanumeric characters, hyphens, and underscores

        :param key: The key to convert to a CSS class name
        :type key: str
        :return: A valid CSS class name
        :rtype: str
        """
        # Replace invalid characters with underscores
        sanitized_key = re.sub(r"[^a-zA-Z0-9_-]", "-", str(key))

        return cls.CSS_PREFIX + sanitized_key

    @classmethod
    def get_page_height(cls, additional_padding: int = 0) -> str:
        """Return the height of the page
        # 8*2px of main padding
        # 16px of main row wrap (of a column)

        :return: _description_
        :rtype: str
        """
        return f"calc(100vh - {32 + additional_padding}px)"

    @classmethod
    def store_uploaded_file_in_tmp_dir(cls, uploaded_file: Any) -> str:
        """Store the uploaded file in a temporary directory

        :param uploaded_file: the uploaded file
        :type uploaded_file: UploadedFile
        :return: the path to the stored file
        :rtype: str
        """
        temp_dir = Settings.make_temp_dir()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return temp_file_path

    @classmethod
    def hide_sidebar_toggle(cls) -> None:
        """Hide the sidebar toggle button, the sidebar will be always expanded"""
        st.markdown(
            """
<style>
/* Hide the toggle default sidebar button in sidebar and outside */
[data-testid="stSidebarHeader"], [data-testid="stSidebarCollapsedControl"]{
    display: none;
}

/* Add top padding in sidebar */
[data-testid="stSidebarNav"] {
    padding-top:1em;
}

/* Always show the sidebar (even in small screen) */
.stSidebar {
    transform: none !important;
    max-width: initial !important;
}

/* Prevent main section to be full width on small screen */
.stMain{
    position: relative;
}
</style>
""",
            unsafe_allow_html=True,
        )

    @classmethod
    def hide_sidebar(cls) -> None:
        if st.session_state.get(cls.SIDEBAR_STATE_KEY) != "collapsed":
            st.session_state[cls.SIDEBAR_STATE_KEY] = "collapsed"
            st.rerun()

    @classmethod
    def show_sidebar(cls) -> None:
        if st.session_state.get(cls.SIDEBAR_STATE_KEY) != "expanded":
            st.session_state[cls.SIDEBAR_STATE_KEY] = "expanded"
            st.rerun()

    @classmethod
    def toggle_sidebar(cls) -> None:
        if st.session_state.get(cls.SIDEBAR_STATE_KEY) == "collapsed":
            cls.show_sidebar()
        else:
            cls.hide_sidebar()

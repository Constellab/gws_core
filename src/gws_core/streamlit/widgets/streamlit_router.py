from typing import Any, Callable, Dict

import streamlit as st


class StreamlitRouter():
    """ A class to manage the routing of pages in a Streamlit app.
    This class allows you to add pages and navigate between them navigate between them.

    :return: _description_
    :rtype: _type_
    """

    pages: Dict[str, Any] = None

    SESSION_KEY = '__gws_streamlit_router__'

    def __init__(self):
        self.pages = {}

    def add_page(self, page_function: Callable[[], None],
                 title: str | None = None,
                 icon: str | None = None,
                 url_path: str | None = None,
                 default: bool = False):

        page_ = st.Page(page_function, title=title, icon=icon, url_path=url_path, default=default)
        self.pages[page_.url_path] = page_

        # save the page in the session state
        st.session_state[self.SESSION_KEY] = self
        return page_

    def run(self):
        # Create a navigation bar with the pages
        pg = st.navigation(list(self.pages.values()))

        # Run the selected page
        pg.run()

    def navigate(self, url_path: str):
        """Navigate to a specific page by its URL path."""
        if url_path in self.pages:
            st.switch_page(self.pages[url_path])
        else:
            st.error(f"Page with URL path '{url_path}' does not exist.")

    def remove_page(self, url_path: str):
        """Remove a page from the router."""
        if url_path in self.pages:
            del self.pages[url_path]
            st.session_state[self.SESSION_KEY] = self
        else:
            st.error(f"Page with URL path '{url_path}' does not exist.")

    def clear(self):
        """Clear all pages from the router."""
        self.pages.clear()
        st.session_state[self.SESSION_KEY] = self

    @staticmethod
    def load_from_session() -> 'StreamlitRouter':
        """Load the router from the session state."""
        if StreamlitRouter.SESSION_KEY not in st.session_state:
            st.session_state[StreamlitRouter.SESSION_KEY] = StreamlitRouter()
        return st.session_state[StreamlitRouter.SESSION_KEY]

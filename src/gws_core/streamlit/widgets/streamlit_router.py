from typing import Any, Callable, Dict

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO


class StreamlitPage(BaseModelDTO):
    page: Any
    url_path: str
    hidden: bool


class StreamlitRouter():
    """ A class to manage the routing of pages in a Streamlit app.
    This class allows you to add pages and navigate between them navigate between them.

    :return: _description_
    :rtype: _type_
    """

    pages: Dict[str, StreamlitPage] = None

    SESSION_KEY = '__gws_streamlit_router__'

    def __init__(self):
        self.pages = {}

    def add_page(self, page_function: Callable[[], None],
                 title: str | None = None,
                 icon: str | None = None,
                 url_path: str | None = None,
                 default: bool = False,
                 hide_from_sidebar: bool = False) -> StreamlitPage:
        """
        Add a page to the router.
        :param page_function: The function that renders the page
        :type page_function: Callable[[], None]
        :param title: The title of the page, defaults to None
        :type title: str | None, optional
        :param icon: The icon of the page, defaults to None
        :type icon: str | None, optional
        :param url_path: The URL path of the page, defaults to None
        :type url_path: str | None, optional
        :param default: Whether the page is the default page, defaults to False
        :type default: bool, optional
        :param hide_from_sidebar: Whether to hide the page from the sidebar. It doesn't work for first, defaults to False
        :type hide_from_sidebar: bool, optional
        :return: The StreamlitPage object
        :rtype: StreamlitPage
        """

        page_ = st.Page(page_function, title=title, icon=icon, url_path=url_path, default=default)
        streamlit_page = StreamlitPage(page=page_,
                                       url_path=url_path,
                                       hidden=hide_from_sidebar)
        self.pages[page_.url_path] = streamlit_page

        # save the page in the session state
        st.session_state[self.SESSION_KEY] = self
        return streamlit_page

    def run(self):
        streamlit_pages = [page for page in self.pages.values()]
        hidden_pages = [page.url_path for page in streamlit_pages if page.hidden]
        self._hide_pages_from_sidebar(hidden_pages)

        # Create a navigation bar with the pages
        pages = [page.page for page in streamlit_pages]
        pg = st.navigation(pages)

        # Run the selected page
        pg.run()

    @classmethod
    def _hide_pages_from_sidebar(cls, pages_to_hide: list[str]) -> None:
        """Hide specific pages from the sidebar navigation

        :param pages_to_hide: List of page names to hide
        :type pages_to_hide: list[str]
        """
        hide_pages_css = """
        <style>
        """

        for page in pages_to_hide:
            # Create a selector that targets the specific page in the navigation
            hide_pages_css += f"""
            [data-testid="stSidebarNav"] ul li a[href*="/{page.lower().replace(' ', '_')}"] {{
                display: none !important;
            }}
            """

        hide_pages_css += """
        </style>
        """

        st.markdown(hide_pages_css, unsafe_allow_html=True)

    def navigate(self, url_path: str):
        """Navigate to a specific page by its URL path."""
        if url_path in self.pages:
            st.switch_page(self.pages[url_path].page)
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

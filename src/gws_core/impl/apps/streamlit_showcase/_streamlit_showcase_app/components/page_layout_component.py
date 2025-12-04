"""Component to provide consistent page layout across showcase pages."""

from typing import Callable

import streamlit as st


def page_layout(
    title: str,
    description: str,
    content_function: Callable,
) -> None:
    """
    Create a consistent page layout with title, description, and content.

    This component provides a standardized layout for all showcase pages including:
    - Page title (large heading)
    - Page description (gray text)
    - Content area with proper spacing

    :param title: The main page title
    :param description: Brief description of the page (displayed in gray)
    :param content_function: A callable that renders the page content when invoked
    """
    # Page header
    st.title(title)

    # Page description with gray color
    st.markdown(
        f'<p style="color: gray; font-size: 1.1rem;">{description}</p>', unsafe_allow_html=True
    )

    # Render page content
    content_function()

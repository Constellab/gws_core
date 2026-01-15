"""Component to display examples with tabs for demo, code, and documentation."""

from collections.abc import Callable

import streamlit as st
from gws_streamlit_main import class_doc_component, method_doc_component


def example_tabs(
    example_function: Callable | None = None,
    code: str | None = None,
    title: str | None = None,
    description: str | None = None,
    doc_func: Callable | list[Callable] | None = None,
    doc_class: type | list[type] | None = None,
) -> None:
    """
    Create a tabbed interface to display an example with its code and documentation.

    This component creates tabs to showcase:
    1. Example - Shows the live interactive component (if example_function is provided)
    2. Code - Displays the source code in a code block (if code is provided)
    3. API - Shows the function/class documentation (if doc_func or doc_class is provided)

    :param example_function: Optional callable that renders the live example when invoked
    :param code: Optional source code as a string to display in the Code tab
    :param title: Optional title for the example section
    :param description: Optional brief description of what the example demonstrates
    :param doc_func: Optional function or list of functions to document in the API tab
    :param doc_class: Optional class or list of classes to document in the API tab
    """
    # Display header (optional)
    if title is not None:
        st.subheader(title)
    if description is not None:
        st.markdown(f'<p style="color: gray;">{description}</p>', unsafe_allow_html=True)

    # Build the tabs list
    tab_names = []
    if example_function is not None:
        tab_names.append("Example")
    if code is not None:
        tab_names.append("Code")
    if doc_func is not None or doc_class is not None:
        tab_names.append("API")

    # Create tabs only if there are any tabs to show
    if not tab_names:
        return

    tabs = st.tabs(tab_names)

    # Track tab index
    tab_index = 0

    # Example tab (if applicable)
    if example_function is not None:
        with tabs[tab_index]:
            # Call the example function to render the live component
            example_function()
        tab_index += 1

    # Code tab (if applicable)
    if code is not None:
        with tabs[tab_index]:
            # Add copy button using Streamlit's built-in functionality
            st.code(code, language="python")
        tab_index += 1

    # API tab (if applicable)
    if doc_func is not None or doc_class is not None:
        with tabs[tab_index]:
            # Render function documentation
            if doc_func is not None:
                # Convert func to list if it's a single callable
                func_list = doc_func if isinstance(doc_func, list) else [doc_func]

                # Render documentation for each function
                for f in func_list:
                    method_doc_component(func=f)

            # Render class documentation
            if doc_class is not None:
                # Convert class to list if it's a single type
                class_list = doc_class if isinstance(doc_class, list) else [doc_class]

                # Render documentation for each class
                for cls in class_list:
                    class_doc_component(class_type=cls)

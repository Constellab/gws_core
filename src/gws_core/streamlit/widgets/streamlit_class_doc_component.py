"""Streamlit component to display class documentation extracted via ReflectorHelper."""

from typing import Optional, Type

import streamlit as st

from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.core.utils.reflector_types import ClassicClassDocDTO

from .streamlit_doc_component import render_method_doc


def class_doc_component(
    class_type: Type,
    title: Optional[str] = None,
    show_description: bool = True,
    show_variables: bool = True,
    show_methods: bool = True,
) -> None:
    """
    Display class documentation in a formatted layout.

    This component extracts documentation from a class using ReflectorHelper.get_class_docs
    and displays it in a styled format using Streamlit's native widgets.

    :param class_type: The class type to document
    :param title: Optional custom title. If None, uses the class name
    :param show_description: Whether to show the class description
    :param show_variables: Whether to show the class variables
    :param show_methods: Whether to show the class methods
    """
    # Extract documentation using ReflectorHelper
    class_doc: Optional[ClassicClassDocDTO] = ReflectorHelper.get_class_docs(class_type)

    if class_doc is None:
        st.error("Unable to extract documentation for this class.")
        return

    # Title
    heading_text = title or class_doc.name
    st.subheader(heading_text)

    # Class description
    if show_description and class_doc.doc:
        st.markdown(class_doc.doc)

    # Variables section
    if show_variables and class_doc.variables:
        st.markdown("### Variables")

        variable_names = []
        variable_types = []

        for var_name, var_type in class_doc.variables.items():
            variable_names.append(f"`{var_name}`")
            variable_types.append(f"`{var_type}`")

        # Display using st.table with dictionary format
        table_data = {
            "Variable": variable_names,
            "Type": variable_types,
        }
        st.table(table_data)

    # Methods section
    if show_methods and class_doc.methods:
        st.markdown("### Methods")

        for method in class_doc.methods:
            with st.expander(f"`{method.name}`"):
                # Use render_method_doc to display the method documentation
                render_method_doc(
                    method_doc=method,
                    title=None,  # No title since we're inside an expander with the method name
                    show_description=True,
                    show_parameters=True,
                    show_return_type=True
                )

"""Streamlit component to display function documentation extracted via ReflectorHelper."""

from collections.abc import Callable

import streamlit as st

from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.core.utils.reflector_types import MethodDoc


def render_method_doc(
    method_doc: MethodDoc,
    title: str | None = None,
    show_description: bool = True,
    show_parameters: bool = True,
    show_return_type: bool = False,
) -> None:
    """
    Render method documentation from a MethodDoc object.

    This function displays method documentation in a formatted table using Streamlit's native widgets.

    :param method_doc: The MethodDoc object containing the documentation
    :param title: Optional custom title. If None, uses the method name
    :param show_description: Whether to show the method description
    :param show_parameters: Whether to show the parameters table
    :param show_return_type: Whether to show the return type
    """
    if method_doc is None:
        st.error("Unable to display documentation - MethodDoc is None.")
        return

    # Title
    heading_text = title or method_doc.name
    st.subheader(heading_text)

    # Function description
    if show_description and method_doc.doc:
        doc_without_args = method_doc.get_doc_without_args()
        if doc_without_args:
            st.markdown(doc_without_args)

    # Parameters table
    if show_parameters:
        if len(method_doc.args) > 0:
            # Create a table for parameters using dictionary format
            parameter_names = []
            types = []
            descriptions = []

            for arg in method_doc.args:
                # Get description from docstring
                arg_description = method_doc.get_arg_description(arg.arg_name)
                if not arg_description:
                    arg_description = "No description provided"

                # Build the description with default value if present
                description_text = arg_description
                if arg.arg_default_value:
                    description_text += f" (default: `{arg.arg_default_value}`)"

                parameter_names.append(f"`{arg.arg_name}`")
                types.append(f"`{arg.arg_type}`")
                descriptions.append(description_text)

            # Display using st.table with dictionary format
            table_data = {"Parameter": parameter_names, "Type": types, "Description": descriptions}
            st.table(table_data)
        elif show_parameters:
            st.text("No parameters.")

    # Return type
    if show_return_type and method_doc.return_type:
        return_description = method_doc.get_return_description()
        return_text = f"**Returns:** `{method_doc.return_type}`"
        if return_description:
            return_text = f"{return_text} - {return_description}"
        st.markdown(return_text)


def method_doc_component(
    func: Callable,
    title: str | None = None,
    show_description: bool = True,
    show_parameters: bool = True,
    show_return_type: bool = False,
) -> None:
    """
    Display function documentation in a formatted table.

    This component extracts documentation from a function using ReflectorHelper.get_func_doc
    and displays it in a styled format using Streamlit's native widgets.

    :param func: The function to document
    :param title: Optional custom title for the card. If None, uses the function name
    :param show_description: Whether to show the function description
    :param show_parameters: Whether to show the parameters table
    :param show_return_type: Whether to show the return type
    """
    # Extract documentation using ReflectorHelper
    func_doc: MethodDoc | None = ReflectorHelper.get_func_doc(func)

    if func_doc is None:
        st.error("Unable to extract documentation for this function.")
        return

    # Use the render_method_doc function to display the documentation
    render_method_doc(
        method_doc=func_doc,
        title=title,
        show_description=show_description,
        show_parameters=show_parameters,
        show_return_type=show_return_type,
    )

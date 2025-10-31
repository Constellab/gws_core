"""Reflex component to display function documentation extracted via ReflectorHelper."""

from typing import Callable, Optional

import reflex as rx

from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.core.utils.reflector_types import MethodDoc


def doc_component(
    func: Callable,
    title: Optional[str] = None,
    show_function_name: bool = True,
    show_description: bool = True,
    show_parameters: bool = True,
    show_return_type: bool = False,
) -> rx.Component:
    """
    Display function documentation in a formatted table.

    This component extracts documentation from a function using ReflectorHelper.get_func_doc
    and displays it in a styled table similar to the Component Properties section in rich_text_page.

    :param func: The function to document
    :param title: Optional custom title for the card. If None, uses "Function Documentation"
    :param show_function_name: Whether to show the function name in the heading
    :param show_description: Whether to show the function description
    :param show_parameters: Whether to show the parameters table
    :param show_return_type: Whether to show the return type
    :return: A Reflex component displaying the function documentation
    """
    # Extract documentation using ReflectorHelper
    func_doc: Optional[MethodDoc] = ReflectorHelper.get_func_doc(func, func.__name__)

    if func_doc is None:
        return rx.card(
            rx.heading(title or "Function Documentation", size="6", margin_bottom="1em"),
            rx.text("Unable to extract documentation for this function.", color="red"),
        )

    # Build the component elements
    elements = []

    # Title
    if show_function_name:
        heading_text = f"{title or 'Function Documentation'}: {func_doc.name}"
    else:
        heading_text = title or "Function Documentation"
    elements.append(rx.heading(heading_text, size="6", margin_bottom="1em"))

    # Function description
    if show_description and func_doc.doc:
        doc_without_args = func_doc.get_doc_without_args()
        if doc_without_args:
            elements.append(rx.text(doc_without_args, margin_bottom="1em"))

    # Parameters table
    if show_parameters and len(func_doc.args) > 0:
        parameter_rows = []
        for arg in func_doc.args:
            # Get description from docstring
            arg_description = func_doc.get_arg_description(arg.arg_name)
            if not arg_description:
                arg_description = "No description provided"

            # Build the description with default value if present
            description_text = arg_description
            if arg.arg_default_value:
                description_text += f" (default: {arg.arg_default_value})"

            parameter_rows.append(
                rx.table.row(
                    rx.table.cell(rx.code(arg.arg_name)),
                    rx.table.cell(rx.code(arg.arg_type)),
                    rx.table.cell(description_text),
                )
            )

        elements.append(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Parameter"),
                        rx.table.column_header_cell("Type"),
                        rx.table.column_header_cell("Description"),
                    ),
                ),
                rx.table.body(*parameter_rows),
                width="100%",
                margin_bottom="1em",
            )
        )
    elif show_parameters:
        elements.append(rx.text("No parameters.", color="gray", margin_bottom="1em"))

    # Return type
    if show_return_type and func_doc.return_type:
        return_description = func_doc.get_return_description()
        return_text = f"Returns: {rx.code(func_doc.return_type)}"
        if return_description:
            return_text = f"{return_text} - {return_description}"
        elements.append(rx.text(return_text, margin_bottom="0.5em"))

    return rx.card(*elements)

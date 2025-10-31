"""Doc component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main import doc_component

from ..components import example_tabs, page_layout


def example_function(name: str, age: int = 25, active: bool = True) -> str:
    """
    This is an example function to demonstrate the doc component.

    This function takes a name and optional age and active status,
    and returns a formatted greeting message.

    :param name: The name of the person to greet
    :param age: The age of the person, defaults to 25
    :param active: Whether the person is active in the system, defaults to True
    :return: A formatted greeting string
    """
    if active:
        return f"Hello {name}, you are {age} years old and active!"
    return f"Hello {name}, you are {age} years old."


def doc_component_page() -> rx.Component:
    """Render the doc component demo page."""

    # Example 1: Using doc_component with example_function
    example1_component = doc_component(
        func=example_function,
        title="Example Function",
        show_description=True,
        show_parameters=True,
        show_return_type=True,
    )

    code1 = """from gws_reflex_main import doc_component

# Define your function with proper docstring
def example_function(name: str, age: int = 25, active: bool = True) -> str:
    \"""
    This is an example function to demonstrate the doc component.

    This function takes a name and optional age and active status,
    and returns a formatted greeting message.

    :param name: The name of the person to greet
    :param age: The age of the person, defaults to 25
    :param active: Whether the person is active in the system, defaults to True
    :return: A formatted greeting string
    \"""
    if active:
        return f"Hello {name}, you are {age} years old and active!"
    return f"Hello {name}, you are {age} years old."

# Display full documentation
doc_component(func=my_function)"""

    return page_layout(
        "Documentation Component",
        "This page demonstrates the documentation component that automatically "
        "generates documentation for functions and components."
        "This is the component used in this app to display function documentation.",

        # Example 1
        example_tabs(
            example_component=example1_component,
            code=code1,
            func=doc_component,
        ),
    )

"""Doc component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main import doc_component


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
    return rx.box(
        rx.heading("Documentation Component", size="9", margin_bottom="0.5em"),

        rx.text(
            "This page demonstrates the documentation component that automatically "
            "extracts and displays function documentation using ReflectorHelper.",
            size="4",
            color="gray",
            margin_bottom="2em",
        ),

        rx.divider(margin_bottom="2em"),

        # Full documentation display
        rx.heading("Full Documentation Display", size="7", margin_bottom="1em"),
        rx.text(
            "The doc_component() function displays complete function documentation including "
            "description, parameters, and return type:",
            margin_bottom="1em",
        ),

        doc_component(
            func=example_function,
            title="Example Function",
            show_function_name=True,
            show_description=True,
            show_parameters=True,
            show_return_type=True,
        ),

        rx.divider(margin_top="2em", margin_bottom="2em"),

        # Usage example
        rx.card(
            rx.heading("Usage Example", size="6", margin_bottom="1em"),

            rx.text(
                "Here's how to use the doc component in your Reflex app:",
                margin_bottom="1em",
            ),

            rx.code_block(
                """from gws_reflex_main import doc_component

# Define your function with proper docstring
def my_function(param1: str, param2: int = 10) -> bool:
    \"\"\"
    Description of what the function does.

    :param param1: Description of param1
    :param param2: Description of param2, defaults to 10
    :return: Description of return value
    \"\"\"
    return True

# Display full documentation
doc_component(func=my_function)
)""",
                language="python",
                margin_bottom="1em",
            ),
        ),

        rx.divider(margin_top="2em", margin_bottom="2em"),

        # Component parameters - using doc_component to document itself!
        rx.heading("doc_component API Documentation", size="7", margin_bottom="1em"),
        rx.text(
            "The component can document itself! Here's the complete API documentation "
            "generated using doc_component:",
            margin_bottom="1em",
        ),

        doc_component(
            func=doc_component,
            show_function_name=False,
        ),

        padding="2em",
    )

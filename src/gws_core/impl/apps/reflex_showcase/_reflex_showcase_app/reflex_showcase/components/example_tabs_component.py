"""Component to display examples with tabs for demo, code, and documentation."""

from typing import Callable, Optional

import reflex as rx
from gws_reflex_main import doc_component


class ExampleTabsState(rx.State):
    """State for the example tabs component."""

    @rx.event
    def copy_code_to_clipboard(self, code: str):
        """
        Copy code to clipboard and show success toast.

        :param code: The code to copy to clipboard
        """
        # Copy to clipboard
        yield rx.set_clipboard(code)
        # Show success toast
        yield rx.toast.success(
            "Code copied to clipboard!",
            duration=3000,
        )


def example_tabs(
    example_component: rx.Component,
    code: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    func: Optional[Callable] = None,
) -> rx.Component:
    """
    Create a tabbed interface to display an example with its code and documentation.

    This component creates a card with three tabs:
    1. Example - Shows the live interactive component
    2. Code - Displays the source code in a code block
    3. API - Shows the function documentation (if func is provided)

    :param example_component: The live Reflex component to display in the Example tab
    :param code: The source code as a string to display in the Code tab
    :param title: Optional title for the example section
    :param description: Optional brief description of what the example demonstrates
    :param func: Optional function to document in the API tab. If None, API tab is hidden
    :return: A Reflex component with tabbed interface
    """
    # Build the tabs list
    tabs_content = [
        rx.tabs.trigger("Example", value="example"),
        rx.tabs.trigger("Code", value="code"),
    ]

    # Add API tab trigger if function is provided
    if func is not None:
        tabs_content.append(rx.tabs.trigger("API", value="api"))

    # Build tab content panels
    tab_panels = [
        # Example tab
        rx.tabs.content(
            rx.box(
                example_component,
                padding="1em",
            ),
            value="example",
        ),
        # Code tab with copy button
        rx.tabs.content(
            rx.box(
                rx.button(
                    rx.icon("clipboard", size=16),
                    rx.text("Copy Code", margin_left="0.5em"),
                    on_click=ExampleTabsState.copy_code_to_clipboard(code),
                    size="2",
                    variant="soft",
                    position="absolute",
                    top="1em",
                    right="1em",
                ),
                rx.code_block(
                    code,
                    language="python",
                ),
                position="relative",
            ),
            value="code",
        ),
    ]

    # Add API tab panel if function is provided
    if func is not None:
        tab_panels.append(
            rx.tabs.content(
                rx.box(
                    doc_component(
                        func=func,
                    ),
                    padding_top="1em",
                ),
                value="api",
            )
        )

    # Build header components (optional)
    header_components = []
    if title is not None:
        header_components.append(rx.heading(title, size="6", margin_bottom="0.5em"))
    if description is not None:
        header_components.append(rx.text(description, margin_bottom="1em", color="gray"))

    return rx.box(
        *header_components,
        rx.tabs.root(
            rx.tabs.list(
                *tabs_content,
            ),
            *tab_panels,
            default_value="example",
            width="100%",
        ),
        width="100%",
        margin_bottom="2em",
    )

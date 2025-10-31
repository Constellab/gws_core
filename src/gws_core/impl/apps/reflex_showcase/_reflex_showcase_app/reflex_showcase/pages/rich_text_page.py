"""Rich text component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main import ReflexMainState, doc_component
from gws_reflex_main.gws_components import rich_text_component

from gws_core.core.utils.logger import Logger
from gws_core.impl.rich_text.rich_text import RichText


class RichTextPageState(ReflexMainState):
    """State for the rich text page."""

    rich_text_output: str = ""

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        """Handle changes from the rich text component."""
        Logger.info(f"Rich text changed: {event_data}")
        self.rich_text_output = str(event_data)


def rich_text_page() -> rx.Component:
    """Render the rich text component demo page."""

    # Create sample rich text content
    rich_text = RichText()
    rich_text.add_paragraph("This is a paragraph of sample text.")
    rich_text.add_paragraph("You can edit this text and add formatting like bold, italic, and more.")
    rich_text.add_formula("E = mc^2")
    rich_text.add_paragraph("The rich text editor supports formulas, lists, and various formatting options.")

    return rx.box(
        rx.heading("Rich Text Editor Component", size="9", margin_bottom="0.5em"),

        rx.text(
            "This page demonstrates the rich text editor component for Reflex applications.",
            size="4",
            color="gray",
            margin_bottom="2em",
        ),

        rx.divider(margin_bottom="2em"),

        # Rich text editor demo
        rx.card(
            rx.heading("Interactive Demo", size="6", margin_bottom="1em"),

            rx.text(
                "Try editing the text below. The component supports rich formatting including "
                "headings, bold, italic, lists, formulas, and more.",
                margin_bottom="1em",
            ),

            rx.box(
                rich_text_component(
                    placeholder="Type something here...",
                    initial_value=rich_text.to_dto(),
                    output_event=RichTextPageState.handle_rich_text_change,
                    min_height="300px",
                ),
                margin_bottom="1em",
            ),

            rx.cond(
                RichTextPageState.rich_text_output != "",
                rx.box(
                    rx.heading("Output Data", size="5", margin_bottom="0.5em"),
                    rx.text("The component outputs data in the following format:"),
                    rx.code_block(
                        RichTextPageState.rich_text_output,
                        language="json",
                        margin_top="0.5em",
                    ),
                    margin_top="2em",
                ),
            ),

            margin_bottom="2em",
        ),

        # Code example
        rx.card(
            rx.heading("Code Example", size="6", margin_bottom="1em"),

            rx.text(
                "Here's how to use the rich text component in your Reflex app:",
                margin_bottom="1em",
            ),

            rx.code_block(
                """from gws_reflex_main.gws_components import rich_text_component
import reflex as rx

# Create initial content
rich_text = RichText()
rich_text.add_paragraph("This is a paragraph")
rich_text.add_heading("Heading Example", level=2)
rich_text.add_formula("E = mc^2")

class MyState(rx.State):
    # Define event handler
    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        print(f"Rich text changed: {event_data}")

# Use the component
rich_text_component(
    placeholder="Type something here...",
    initial_value=rich_text.to_dto(),
    output_event=MyState.handle_rich_text_change,
    min_height="300px",
)""",
                language="python",
                margin_bottom="1em",
            ),

            margin_bottom="2em",
        ),

        # Component properties - using doc_component for automatic documentation
        rx.heading("Component API", size="6", margin_bottom="1em"),
        rx.text(
            "The rich_text_component is automatically documented using doc_component:",
            margin_bottom="1em",
        ),

        doc_component(
            func=rich_text_component,
            show_function_name=False,
        ),

        padding="2em",
    )

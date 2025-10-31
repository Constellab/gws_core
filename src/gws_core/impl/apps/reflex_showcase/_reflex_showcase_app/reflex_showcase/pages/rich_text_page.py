"""Rich text component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main import ReflexMainState
from gws_reflex_main.gws_components import rich_text_component

from gws_core.core.utils.logger import Logger
from gws_core.impl.rich_text.rich_text import RichText

from ..components import example_tabs, page_layout


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

    # Example component
    example_component = rx.box(
        rich_text_component(
            placeholder="Type something here...",
            initial_value=rich_text.to_dto(),
            output_event=RichTextPageState.handle_rich_text_change,
            min_height="500px",
        ),
        rx.cond(
            RichTextPageState.rich_text_output != "",
            rx.box(
                rx.heading("Output Data", size="5", margin_bottom="0.5em", margin_top="1em"),
                rx.text("The component outputs data in the following format:"),
                rx.code_block(
                    RichTextPageState.rich_text_output,
                    language="json",
                    margin_top="0.5em",
                ),
            ),
        ),
    )

    # Code example
    code_example = """from gws_reflex_main.gws_components import rich_text_component
from gws_reflex_main import ReflexMainState
import reflex as rx
from gws_core import RichText, RichTextDTO

# Create initial content
rich_text = RichText()
rich_text.add_paragraph("This is a paragraph")
rich_text.add_formula("E = mc^2")

class MyState(ReflexMainState):

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        print("Rich text changed:", RichTextDTO.from_json(event_data))

# Use the component
rich_text_component(
    placeholder="Type something here...",
    initial_value=rich_text.to_dto(),
    output_event=MyState.handle_rich_text_change,
    min_height="500px",
)"""

    # Rich text editor demo with tabs
    return page_layout(
        "Rich Text Editor Component",
        "This page demonstrates the rich text editor component for Reflex applications. The component supports rich formatting including "
        "headings, bold, italic, lists, formulas, and more.",
        example_tabs(
            example_component=example_component,
            code=code_example,
            func=rich_text_component,
        ),
    )

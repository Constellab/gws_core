"""Rich text component demo page for the Reflex showcase app."""

import reflex as rx
from gws_core import RichText, RichTextDTO
from gws_core.note.note_dto import NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_reflex_main import ReflexMainState
from gws_reflex_main.gws_components import rich_text_component

from ..components import example_tabs, page_layout

default_rich_text = RichText()
default_rich_text.add_paragraph("This is a paragraph of sample text.")
default_rich_text.add_paragraph(
    "You can edit this text and add formatting like bold, italic, and more."
)
default_rich_text.add_formula("E = mc^2")
default_rich_text.add_paragraph(
    "The rich text editor supports formulas, lists, and various formatting options."
)


class RichTextPageState(rx.State):
    """State for the rich text page."""

    _rich_text: RichText = default_rich_text

    @rx.event
    def reset_rich_text(self):
        """Initialize the state."""
        self._rich_text = default_rich_text

    @rx.var
    def rich_text(self) -> RichTextDTO:
        """Get the current rich text as a DTO."""
        return self._rich_text.to_dto()

    @rx.var
    def is_not_empty(self) -> bool:
        """Check if the rich text is empty."""
        return not self._rich_text.is_empty()

    @rx.var
    def rich_text_string(self) -> str:
        """Get the current rich text as a JSON string."""
        return self._rich_text.to_dto().to_json_str()

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        """Handle changes from the rich text component."""
        self._rich_text = RichText.from_json(event_data)

    @rx.event
    async def save_as_note(self):
        """Save the rich text content as a note in the user's account."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            note = NoteService.create(NoteSaveDTO(title="Rich Text Content"))
            NoteService.update_content(note.id, self._rich_text.to_dto())


def rich_text_page() -> rx.Component:
    """Render the rich text component demo page."""

    # Example component
    example_component = rx.box(
        rich_text_component(
            placeholder="Type something here...",
            value=RichTextPageState.rich_text,
            output_event=RichTextPageState.handle_rich_text_change,
            use_custom_tools=True,
        ),
        rx.cond(
            RichTextPageState.is_not_empty,
            rx.box(
                rx.heading("Output Data", size="5", margin_bottom="0.5em", margin_top="1em"),
                rx.text("The component outputs data in the following format:"),
                rx.code_block(
                    RichTextPageState.rich_text_string,
                    language="json",
                    margin_top="0.5em",
                ),
            ),
            rx.text("The rich text is currently empty.", color="gray", margin_top="1em"),
        ),
        rx.button("Reset Content", on_click=RichTextPageState.reset_rich_text, margin_top="1em"),
        rx.button(
            "Save as Note",
            on_click=RichTextPageState.save_as_note,
            margin_top="1em",
            margin_left="1em",
        ),
    )

    # Code example
    code_example = """from gws_reflex_main import ReflexMainState
from gws_reflex_main.gws_components import rich_text_component
from gws_core import RichText, RichTextDTO
import reflex as rx

# Create default content
default_rich_text = RichText()
default_rich_text.add_paragraph("This is a paragraph of sample text.")
default_rich_text.add_formula("E = mc^2")

class MyState(rx.State):
    _rich_text: RichText = default_rich_text

    @rx.var
    def rich_text(self) -> RichTextDTO:
        \"\"\"Get the current rich text as a DTO.\"\"\"
        return self._rich_text.to_dto()

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        \"\"\"Handle changes from the rich text component.\"\"\"
        self._rich_text = RichText.from_json(event_data)

    @rx.event
    def reset_rich_text(self):
        \"\"\"Reset to default content.\"\"\"
        self._rich_text = default_rich_text

# Use the component
rx.box(
    rich_text_component(
        placeholder="Type something here...",
        value=MyState.rich_text,
        output_event=MyState.handle_rich_text_change,
    ),
    rx.button("Reset Content",
              on_click=MyState.reset_rich_text,
              margin_top="1em"),
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

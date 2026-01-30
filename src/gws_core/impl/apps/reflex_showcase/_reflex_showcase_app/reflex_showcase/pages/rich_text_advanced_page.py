"""Rich text component with custom tools demo page for the Reflex showcase app."""

from pathlib import Path

import reflex as rx
from gws_core import RichText, RichTextBlock, RichTextDTO
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataSpecial
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator
from gws_reflex_main.gws_components import RichTextCustomBlocksConfig, rich_text_component

from ..components import example_tabs, page_layout

asset_path = rx.asset("rich_text_extension.js", shared=True)

js_file_content = Path(__file__).parent.joinpath("rich_text_extension.js").read_text()


@rich_text_block_decorator("CustomBlock", human_name="Custom Block")
class CustomBlock(RichTextBlockDataSpecial):
    text: str

    def to_html(self) -> str:
        return f"<p>Custom Block: {self.text}</p>"

    def to_markdown(self) -> str:
        """Convert the block to markdown for export."""
        return ""


default_advanced_rich_text = RichText()
default_advanced_rich_text.add_paragraph("This is a paragraph of sample text.")
default_advanced_rich_text.append_block(
    RichTextBlock.from_data(CustomBlock(text="This is a custom block added to the rich text."))
)
default_advanced_rich_text.add_paragraph("End.")


class RichTextAdvancedPageState(rx.State):
    """State for the advanced rich text page."""

    _rich_text: RichText = default_advanced_rich_text

    @rx.event
    def reset_rich_text(self):
        """Initialize the state."""
        self._rich_text = default_advanced_rich_text

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
        return self._rich_text.to_dto().model_dump_json(indent=2)

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        """Handle changes from the rich text component."""
        self._rich_text = RichText.from_json(event_data)


def rich_text_advanced_page() -> rx.Component:
    """Render the rich text component demo page with custom tools."""

    # Example component
    example_component = rx.box(
        rich_text_component(
            placeholder="Type something here...",
            value=RichTextAdvancedPageState.rich_text,
            output_event=RichTextAdvancedPageState.handle_rich_text_change,
            custom_tools_config=RichTextCustomBlocksConfig(
                jsx_file_path=asset_path,
                custom_blocks={"CustomBlock": CustomBlock},
            ),
        ),
        rx.cond(
            RichTextAdvancedPageState.is_not_empty,
            rx.box(
                rx.heading("Output Data", size="5", margin_bottom="0.5em", margin_top="1em"),
                rx.text("The component outputs data in the following format:"),
                rx.code_block(
                    RichTextAdvancedPageState.rich_text_string,
                    language="json",
                    margin_top="0.5em",
                    max_height="400px",
                ),
            ),
            rx.text("The rich text is currently empty.", color="gray", margin_top="1em"),
        ),
        rx.button(
            "Reset Content", on_click=RichTextAdvancedPageState.reset_rich_text, margin_top="1em"
        ),
    )

    # Code example
    code_example = """@rich_text_block_decorator("CustomBlock", human_name="Custom Block")
class CustomBlock(RichTextBlockDataSpecial):
    text: str

    def to_html(self) -> str:
        return f"<p>Custom Block: {self.text}</p>"

    def to_markdown(self) -> str:
        return ""


asset_path = rx.asset("rich_text_extension.js", shared=True)


class MyState(rx.State):

    _rich_text: RichText = RichText()

    @rx.var
    def rich_text(self) -> RichTextDTO:
        return self._rich_text.to_dto()

    @rx.var
    def rich_text_string(self) -> str:
        return self._rich_text.to_dto().model_dump_json(indent=2)

    @rx.event
    def handle_rich_text_change(self, event_data: dict):
        self._rich_text = RichText.from_json(event_data)


rich_text_component(
    placeholder="Type something here...",
    value=MyState.rich_text,
    output_event=MyState.handle_rich_text_change,
    custom_tools_config=RichTextCustomBlocksConfig(
        jsx_file_path=asset_path,
        custom_blocks={"CustomBlock": CustomBlock},
    ),
)"""

    # Rich text editor demo with tabs
    return page_layout(
        "Rich Text Editor Component with Custom Tools",
        "This page demonstrates the rich text editor component for Reflex applications using custom tools."
        + " It defines a block in the python code and the corresponding editor tool in JSX."
        + " It uses the editorjs library: https://editorjs.io/.",
        example_tabs(
            example_component=example_component,
            code=code_example,
            func=rich_text_component,
            additional_tabs=[
                (
                    "JS Component",
                    rx.code_block(
                        js_file_content,
                        language="javascript",
                    ),
                ),
            ],
        ),
    )

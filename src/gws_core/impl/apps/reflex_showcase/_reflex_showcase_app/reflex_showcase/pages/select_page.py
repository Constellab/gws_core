"""Single-select component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main.gws_components import select_component

from ..components import example_tabs, page_layout


class SelectPageState(rx.State):
    """State for the single-select demo page."""

    # Options as a plain list of strings.
    fruit_options: list[str] = ["Apple", "Banana", "Cherry", "Grape", "Mango", "Orange"]

    # One selected value per example so they don't interfere with each other.
    selected_fruit_basic: str = "Apple"
    selected_fruit_search: str = ""

    # {value, label} dict options: displayed label differs from stored value.
    color_options: list[dict] = [
        {"value": "red", "label": "Red"},
        {"value": "green", "label": "Green"},
        {"value": "blue", "label": "Blue"},
        {"value": "yellow", "label": "Yellow"},
    ]
    selected_color: str = ""

    @rx.event
    def set_selected_fruit_basic(self, value: str):
        """Update the selected fruit (basic example)."""
        self.selected_fruit_basic = value

    @rx.event
    def set_selected_fruit_search(self, value: str):
        """Update the selected fruit (searchable example)."""
        self.selected_fruit_search = value

    @rx.event
    def set_selected_color(self, value: str):
        """Update the selected color."""
        self.selected_color = value


def select_page() -> rx.Component:
    """Render the single-select component demo page."""

    # Example 1: Basic single select (searchable defaults to False -> plain dropdown).
    example1_component = rx.vstack(
        select_component(
            label="Fruit",
            placeholder="Select a fruit...",
            data=SelectPageState.fruit_options,
            value=SelectPageState.selected_fruit_basic,
            on_change=SelectPageState.set_selected_fruit_basic,
        ),
        rx.text(
            "Selected: ",
            SelectPageState.selected_fruit_basic,
            size="2",
            color="gray",
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code1 = """import reflex as rx
from gws_reflex_main.gws_components import select_component


class MyState(rx.State):
    fruit_options: list[str] = ["Apple", "Banana", "Cherry", "Grape"]
    selected_fruit: str = "Apple"

    @rx.event
    def set_selected_fruit(self, value: str):
        self.selected_fruit = value


# Basic single select: searchable defaults to False, so it is a plain dropdown
select_component(
    label="Fruit",
    placeholder="Select a fruit...",
    data=MyState.fruit_options,
    value=MyState.selected_fruit,
    on_change=MyState.set_selected_fruit,
)"""

    # Example 2: Same select, made searchable (integrated search field). The single
    # chevron rotates from down to up when the dropdown opens.
    example2_component = rx.vstack(
        select_component(
            label="Fruit",
            placeholder="Search a fruit...",
            data=SelectPageState.fruit_options,
            value=SelectPageState.selected_fruit_search,
            on_change=SelectPageState.set_selected_fruit_search,
            searchable=True,
            nothing_found_message="No fruit found",
        ),
        rx.text(
            "Selected: ",
            SelectPageState.selected_fruit_search,
            size="2",
            color="gray",
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code2 = """# Set searchable=True to add the integrated type-to-filter text field.
# The single chevron rotates down -> up when the dropdown opens.
select_component(
    label="Fruit",
    placeholder="Search a fruit...",
    data=MyState.fruit_options,
    value=MyState.selected_fruit,
    on_change=MyState.set_selected_fruit,
    searchable=True,                       # adds the search field
    nothing_found_message="No fruit found",
)"""

    # Example 3: {value, label} dict options; the label shown differs from the stored value.
    example3_component = rx.vstack(
        rx.text(
            "Options are {value, label} dicts, so the displayed label differs "
            "from the stored value:",
            size="2",
            color="gray",
        ),
        select_component(
            label="Color",
            placeholder="Pick a color",
            data=SelectPageState.color_options,
            value=SelectPageState.selected_color,
            on_change=SelectPageState.set_selected_color,
        ),
        rx.text(
            "Selected value: ",
            SelectPageState.selected_color,
            size="2",
            color="gray",
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code3 = """# Options as {value, label} dicts: label shown != value stored
class MyState(rx.State):
    color_options: list[dict] = [
        {"value": "red", "label": "Red"},
        {"value": "green", "label": "Green"},
        {"value": "blue", "label": "Blue"},
    ]
    selected_color: str = ""

    @rx.event
    def set_selected_color(self, value: str):
        self.selected_color = value


select_component(
    label="Color",
    placeholder="Pick a color...",
    data=MyState.color_options,
    value=MyState.selected_color,
    on_change=MyState.set_selected_color,
)"""

    return page_layout(
        "Select Component",
        "This page demonstrates the single-select component: a dropdown for picking one "
        "value, built on Mantine's Select. It is a plain dropdown by default; set "
        "searchable=True to add an integrated text field that filters the options as you type.",
        # Basic (non-searchable) single-select example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="select_component",
            description="A plain single select over a list of string options (searchable "
            "defaults to False). The on_change handler receives the newly selected value.",
            func=select_component,
        ),
        # Searchable variant
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="Searchable",
            description="The same select with searchable=True, which adds an integrated "
            "text field to filter the options as you type. Focusing the input clears the "
            "visible text so you can type straight away; the current selection is kept "
            "(its label comes back on blur if you don't pick anything else). Use this when "
            "the whole list of options is small (up to ~100 options) and loaded in the "
            "browser up front. Typing just filters that in-memory list, no server call.",
            func=select_component,
        ),
        # Dict options
        example_tabs(
            example_component=example3_component,
            code=code3,
            title="Dict options",
            description="Options can be {value, label} dicts so the displayed label differs "
            "from the stored value: on_change still receives the value, not the label.",
            func=select_component,
        ),
    )

"""Multi-select component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main.gws_components import multi_select_component

from ..components import example_tabs, page_layout


class MultiSelectPageState(rx.State):
    """State for the multi-select demo page."""

    # Basic example: options as a plain list of strings.
    fruit_options: list[str] = ["Apple", "Banana", "Cherry", "Grape", "Mango", "Orange"]
    selected_fruits: list[str] = ["Apple", "Cherry"]

    # max_values example: options as {value, label} dicts.
    color_options: list[dict] = [
        {"value": "red", "label": "Red"},
        {"value": "green", "label": "Green"},
        {"value": "blue", "label": "Blue"},
        {"value": "yellow", "label": "Yellow"},
    ]
    selected_colors: list[str] = []

    @rx.event
    def set_selected_fruits(self, value: list[str]):
        """Update the selected fruits."""
        self.selected_fruits = value

    @rx.event
    def set_selected_colors(self, value: list[str]):
        """Update the selected colors."""
        self.selected_colors = value


def multi_select_page() -> rx.Component:
    """Render the multi-select component demo page."""

    # Example 1: Basic searchable, clearable multi-select over a list of strings.
    example1_component = rx.vstack(
        multi_select_component(
            label="Fruits",
            placeholder="Select fruits...",
            data=MultiSelectPageState.fruit_options,
            value=MultiSelectPageState.selected_fruits,
            on_change=MultiSelectPageState.set_selected_fruits,
            searchable=True,
            clearable=True,
        ),
        rx.text(
            "Selected: ",
            MultiSelectPageState.selected_fruits.join(", "),
            size="2",
            color="gray",
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code1 = """import reflex as rx
from gws_reflex_main.gws_components import multi_select_component


class MyState(rx.State):
    fruit_options: list[str] = ["Apple", "Banana", "Cherry", "Grape"]
    selected_fruits: list[str] = ["Apple", "Cherry"]

    @rx.event
    def set_selected_fruits(self, value: list[str]):
        self.selected_fruits = value


# Basic usage: options as a list of strings
multi_select_component(
    label="Fruits",
    placeholder="Select fruits...",
    data=MyState.fruit_options,
    value=MyState.selected_fruits,
    on_change=MyState.set_selected_fruits,
    searchable=True,
    clearable=True,
)"""

    # Example 2: {value, label} dict options with a max_values cap.
    example2_component = rx.vstack(
        rx.text(
            "Options are {value, label} dicts and at most 2 can be picked:",
            size="2",
            color="gray",
        ),
        multi_select_component(
            label="Colors",
            placeholder="Pick up to 2 colors...",
            data=MultiSelectPageState.color_options,
            value=MultiSelectPageState.selected_colors,
            on_change=MultiSelectPageState.set_selected_colors,
            searchable=True,
            clearable=True,
            max_values=2,
        ),
        rx.text(
            "Selected values: ",
            MultiSelectPageState.selected_colors.join(", "),
            size="2",
            color="gray",
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code2 = """# Options as {value, label} dicts, capped to 2 selections
class MyState(rx.State):
    color_options: list[dict] = [
        {"value": "red", "label": "Red"},
        {"value": "green", "label": "Green"},
        {"value": "blue", "label": "Blue"},
    ]
    selected_colors: list[str] = []

    @rx.event
    def set_selected_colors(self, value: list[str]):
        self.selected_colors = value


multi_select_component(
    label="Colors",
    placeholder="Pick up to 2 colors...",
    data=MyState.color_options,
    value=MyState.selected_colors,
    on_change=MyState.set_selected_colors,
    searchable=True,
    clearable=True,
    max_values=2,  # cap the number of picked values
)"""

    return page_layout(
        "Multi-Select Component",
        "This page demonstrates the multi-select component: a searchable dropdown for "
        "picking several values, built on Mantine's MultiSelect.",
        # Basic multi-select example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="multi_select_component",
            description="A searchable, clearable multi-select over a list of string options. "
            "The on_change handler receives the new list of selected values.",
            func=multi_select_component,
        ),
        # Dict options with max_values
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="Dict options & max_values",
            description="Options can be {value, label} dicts so the displayed label differs "
            "from the stored value, and max_values caps how many can be selected.",
            func=multi_select_component,
        ),
    )

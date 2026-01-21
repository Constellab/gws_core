"""Resource components demo page for the Reflex showcase app."""

import reflex as rx
from gws_core import ResourceModel, ResourceSearchBuilder, Table
from gws_reflex_main import (
    ResourceSelectState,
    resource_select_button,
)

from ..components import example_tabs, page_layout


class ResourceComponentsPageState(rx.State):
    """State for the resource components page."""

    selected_resource_name: str = ""


class DemoResourceSelectState(ResourceSelectState, ResourceComponentsPageState):
    """Demo state for resource selection."""

    async def on_resource_selected(self, resource_model: ResourceModel):
        """Handle resource selection."""
        self.selected_resource_name = resource_model.name


class FilteredResourceSelectState(ResourceSelectState, ResourceComponentsPageState):
    """Demo state for filtered resource selection (flagged only)."""

    async def on_resource_selected(self, resource_model: ResourceModel):
        """Handle resource selection."""
        self.selected_resource_name = resource_model.name

    async def create_search_builder(self) -> ResourceSearchBuilder:
        """Create search builder with custom filter for flagged resources only."""
        search_builder = await super().create_search_builder()
        # This example already filters for flagged by default
        # You could add additional filters here, such as:
        search_builder.add_resource_types_and_sub_types_filter([Table])
        return search_builder


def resource_components_page() -> rx.Component:
    """Render the resource components demo page."""

    # Example 1: Basic resource_select_button
    example1_component = rx.vstack(
        rx.text(
            "Click the button below to open the resource selection dialog:", margin_bottom="0.5em"
        ),
        resource_select_button(state=DemoResourceSelectState),
        rx.cond(
            ResourceComponentsPageState.selected_resource_name != "",
            rx.box(
                rx.text(
                    f"Selected Resource: {ResourceComponentsPageState.selected_resource_name}",
                ),
                margin_top="1em",
                padding="1em",
                border_radius="0.5em",
                bg=rx.color("accent", 2),
            ),
        ),
        align="start",
    )

    code1 = """from gws_reflex_main import resource_select_button, ResourceSelectState, ReflexMainState
from gws_core.resource.resource_model import ResourceModel
import reflex as rx

class MyState(rx.State):
    selected_resource_name: str = ""

class MyResourceSelectState(ResourceSelectState, MyState):
    async def on_resource_selected(self, resource_model: ResourceModel):
        \"\"\"Handle resource selection.\"\"\"
        self.selected_resource_name = resource_model.name

# Display resource select button
resource_select_button(state=MyResourceSelectState)"""

    # Example 2: Resource select with custom filters
    example2_component = rx.vstack(
        rx.text("This example shows a resource selector with custom filters:"),
        rx.text(
            "(The dialog filters resources based on custom criteria)",
            size="2",
            color="gray",
            margin_bottom="0.5em",
        ),
        resource_select_button(state=FilteredResourceSelectState),
        align="start",
    )

    code2 = """from gws_reflex_main import ResourceSelectState, resource_select_button
from gws_core import ResourceModel, ResourceSearchBuilder

class FilteredResourceSelectState(ResourceSelectState):
    async def on_resource_selected(self, resource_model: ResourceModel):
        \"\"\"Handle resource selection.\"\"\"
        self.selected_resource_name = resource_model.name

    async def create_search_builder(self) -> ResourceSearchBuilder:
        \"\"\"Override to add custom filters.\"\"\"
        search_builder = await super().create_search_builder()
        # Add custom filter to only include only Table resources
        search_builder.add_resource_types_and_sub_types_filter([Table])
        return search_builder

# Display filtered resource select button
resource_select_button(state=FilteredResourceSelectState)"""

    return page_layout(
        "Resource Components",
        "This page demonstrates resource selection components for searching and selecting resources from the database.",
        # Basic resource_select_button example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="resource_select_button",
            description="A button that opens a dialog for searching and selecting resources. "
            "The dialog includes filters for name, flagged status, and archived status, "
            "with paginated results.",
            func=resource_select_button,
        ),
        # Filtered resource_select_button example
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="Custom Filters",
            description="Extend ResourceSelectState and override create_search_builder() to add custom "
            "filters such as filtering by specific resource types.",
            func=resource_select_button,
        ),
    )

"""Resource selection component with search dialog."""

import reflex as rx
from gws_reflex_base import dialog_header

from gws_core.resource.resource_dto import ResourceModelDTO

from ..reflex_user_components import user_profile_picture
from .resource_select_state import ResourceSelectState


def resource_select_button(state: type[ResourceSelectState] = ResourceSelectState) -> rx.Component:
    """Button component to open the resource selection dialog.

    Args:
        state: The state class to use for the dialog (should extend ResourceSelectState).
               Defaults to ResourceSelectState.

    Returns:
        A button that when clicked opens a dialog for searching
        and selecting resources from the database.

    Note:
        Pass a custom state that extends ResourceSelectState to handle selection logic.

    Example:
        ```python
        from gws_core import ResourceModel
        from gws_reflex_main import resource_select_button, ResourceSelectState

        # In your state class that extends ResourceSelectState
        class MyResourceState(ResourceSelectState):

            async def on_resource_selected(self, resource_model: ResourceModel):
                # Handle your custom logic
                print(f"Selected: {resource_model.name}")

            # (Optional) Override search builder to filter resource types
            async def create_search_builder(self) -> ResourceSearchBuilder:
                    search_builder = await super().create_search_builder()
                    # Add custom filter to only include resources of a specific type
                    search_builder.add_resource_types_and_sub_types_filter([MyResourceType])
                    return search_builder

        # In your component
        resource_select_button(state=MyResourceState)
        ```
    """
    return rx.fragment(
        rx.button(
            rx.icon("folder-search", size=18),
            "Select Resource",
            on_click=state.open_dialog,
            variant="outline",
        ),
        _resource_select_dialog(state=state),
    )


def _filter_form(state: type[ResourceSelectState]) -> rx.Component:
    """Create the filter form with name, flagged, and archived filters.

    The form auto-submits when checkbox values change.
    """
    return rx.form(
        rx.hstack(
            # Name filter
            rx.input(
                placeholder="Search by name...",
                name="name_filter",
                default_value=state.name_filter,
                width="300px",
            ),
            # Include not flagged checkbox
            rx.checkbox(
                "Include not flagged resources",
                name="include_not_flagged",
                default_checked=state.include_not_flagged,
                on_change=lambda _: rx.call_script(
                    "document.getElementById('resource-search-form').requestSubmit()"
                ),
            ),
            # Include archived checkbox
            rx.checkbox(
                "Include archived resources",
                name="include_archived",
                default_checked=state.include_archived,
                on_change=lambda _: rx.call_script(
                    "document.getElementById('resource-search-form').requestSubmit()"
                ),
            ),
            # Search button
            rx.button(
                rx.icon("search", size=18),
                "Search",
                type="submit",
                disabled=state.is_loading,
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        on_submit=state.search_resources,
        width="100%",
        id="resource-search-form",
    )


def _resource_table_row(
    resource: ResourceModelDTO, state: type[ResourceSelectState]
) -> rx.Component:
    """Create a table row for a single resource.

    Args:
        resource: The resource DTO to display
        state: The state class to use for event handlers

    Returns:
        A table row component with resource information
    """
    return rx.table.row(
        rx.table.cell(rx.text(resource.name, weight="medium")),
        rx.table.cell(
            rx.text(
                rx.cond(resource.resource_type, resource.resource_type.human_name, ""),
                size="2",
                color="gray",
            )
        ),
        rx.table.cell(
            rx.hstack(
                user_profile_picture(resource.last_modified_by),
                rx.moment(
                    resource.last_modified_at,
                    format="YYYY-MM-DD HH:mm",
                    size="2",
                    color="gray",
                ),
                align_items="center",
            )
        ),
        rx.table.cell(
            rx.button(
                "Select",
                on_click=lambda: state.select_resource(resource.id),
                size="2",
                variant="soft",
            )
        ),
    )


def _resource_table(state: type[ResourceSelectState]) -> rx.Component:
    """Create the table displaying search results with load more button."""
    return rx.cond(
        state.is_loading,
        # Loading state
        rx.center(
            rx.spinner(size="3"),
            padding="2em",
            flex="1",
            width="100%",
        ),
        # Table with results
        rx.cond(
            state.resources.length() > 0,
            # Results table with load more button inside scroll area
            rx.scroll_area(
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Name"),
                                rx.table.column_header_cell("Resource Type"),
                                rx.table.column_header_cell("Last Modified"),
                                rx.table.column_header_cell("Actions"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                state.resources,
                                lambda resource: _resource_table_row(resource, state),
                            )
                        ),
                        variant="surface",
                        width="100%",
                    ),
                    # Load more section
                    rx.cond(
                        state.has_more_pages,
                        rx.center(
                            rx.button(
                                rx.cond(
                                    state.is_loading_more,
                                    rx.spinner(size="2"),
                                    rx.text("Load More"),
                                ),
                                on_click=state.load_more_resources,
                                variant="soft",
                                disabled=state.is_loading_more,
                            ),
                            width="100%",
                            margin_top="1em",
                        ),
                        rx.center(
                            rx.text(
                                f"All {state.total_items} resources loaded",
                                size="2",
                                color="gray",
                            ),
                            width="100%",
                            margin_top="1em",
                        ),
                    ),
                    width="100%",
                    spacing="0",
                ),
                type="auto",
                scrollbars="vertical",
                style={"height": "100%"},
                flex="1",
            ),
            # No results message
            rx.center(
                rx.text(
                    "No resources found. Try adjusting your filters.",
                    color="gray",
                    size="2",
                ),
                padding="2em",
                flex="1",
            ),
        ),
    )


def _resource_select_dialog(state: type[ResourceSelectState] = ResourceSelectState) -> rx.Component:
    """Dialog component for searching and selecting resources.

    Args:
        state: The state class to use for the dialog (should extend ResourceSelectState).
               Defaults to ResourceSelectState.

    Displays a dialog with:
    - Header with title and close button
    - Filter row with name, flagged, and archived filters
    - Table showing search results with name, type, and last modified date
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                dialog_header(
                    title="Select Resource",
                    close=state.close_dialog,
                ),
                # Filters
                _filter_form(state),
                # Results table
                _resource_table(state),
                spacing="4",
                width="100%",
                height="100%",
            ),
            max_width="900px",
            height="80vh",
            padding="1.5em",
            style={"display": "flex", "flexDirection": "column"},
        ),
        open=state.dialog_opened,
    )

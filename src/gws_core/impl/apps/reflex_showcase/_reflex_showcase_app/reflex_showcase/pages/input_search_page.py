"""Input search component demo page for the Reflex showcase app."""

import reflex as rx
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
from gws_reflex_main.gws_components import InputSearchResultDTO, input_search_component

from ..components import example_tabs, page_layout


class SearchParam(BaseModelDTO):
    search_text: str
    page: int
    page_size: int


class InputSearchPageState(rx.State):
    """State for the input search page."""

    selected_resource: InputSearchResultDTO | None = None
    resources: PageDTO

    @rx.event
    def search(self, query: dict):
        """Search resources based on the query.

        :param query: The search query
        """
        search_object = SearchParam.from_json(query)

        resources_search_builder = ResourceSearchBuilder()
        resources_search_builder.add_name_filter(search_object.search_text)
        result = resources_search_builder.search_page(
            page=search_object.page, number_of_items_per_page=search_object.page_size
        )

        self.resources = result.map_page(
            lambda resource: InputSearchResultDTO(
                id=resource.id, display_text=resource.name, object=resource.to_dto()
            )
        )

    @rx.event
    def select_item(self, item: dict):
        """Handle item selection.

        :param item: The selected item
        """
        self.selected_resource = InputSearchResultDTO.from_json(item)


class InputSearchPageState2(rx.State):
    """State for the second input search example."""

    selected_resource: InputSearchResultDTO | None = None
    resources: PageDTO

    @rx.event
    def search(self, query: dict):
        """Search resources based on the query."""
        search_object = SearchParam.from_json(query)

        resources_search_builder = ResourceSearchBuilder()
        resources_search_builder.add_name_filter(search_object.search_text)
        result = resources_search_builder.search_page(
            page=search_object.page, number_of_items_per_page=search_object.page_size
        )

        self.resources = result.map_page(
            lambda resource: InputSearchResultDTO(
                id=resource.id, display_text=resource.name, object=resource.to_dto()
            )
        )

    @rx.event
    def select_item(self, item: dict):
        """Handle item selection."""
        self.selected_resource = InputSearchResultDTO.from_json(item)


def input_search_page() -> rx.Component:
    """Render the input search component demo page."""

    # Example 1: Basic input search component
    example1_component = rx.vstack(
        rx.text(
            "Type in the input below to search for resources:",
            margin_bottom="0.5em",
        ),
        input_search_component(
            search_result=InputSearchPageState.resources,
            selected_item=InputSearchPageState.selected_resource,
            item_selected=InputSearchPageState.select_item,
            search_trigger=InputSearchPageState.search,
            placeholder="Search for resources...",
        ),
        align="start",
        width="100%",
    )

    code1 = """from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
import reflex as rx

from .reflex_input_search_component import input_search_component


class SearchParam(BaseModelDTO):
    search_text: str
    page: int
    page_size: int


class MyState(rx.State):
    selected_resource: dict | None = None
    resources: PageDTO

    @rx.event
    def search(self, query: dict):
        search_object = SearchParam.from_json(query)
        resources_search_builder = ResourceSearchBuilder()
        resources_search_builder.add_name_filter(search_object.search_text)
        result = resources_search_builder.search_page(
            page=search_object.page,
            number_of_items_per_page=search_object.page_size
        )
        self.resources = result.to_dto()

    @rx.event
    def select_item(self, item: dict):
        self.selected_resource = item


# Basic usage
input_search_component(
    search_result=MyState.resources,
    selected_item=MyState.selected_resource,
    item_selected=MyState.select_item,
    search_trigger=MyState.search,
    placeholder="Search for resources...",
)"""

    # Example 2: Input search with custom configuration
    example2_component = rx.vstack(
        rx.text(
            "This example shows custom configuration with search on focus:",
            margin_bottom="0.5em",
        ),
        rx.text(
            "(Search triggers on focus and requires only 1 character)",
            size="2",
            color="gray",
            margin_bottom="0.5em",
        ),
        input_search_component(
            search_result=InputSearchPageState2.resources,
            selected_item=InputSearchPageState2.selected_resource,
            item_selected=InputSearchPageState2.select_item,
            search_trigger=InputSearchPageState2.search,
            placeholder="Click to search...",
            min_input_search_length=1,
            init_search_on_focus=True,
            page_size=10,
        ),
        align="start",
        width="100%",
    )

    code2 = """# Custom configuration example
input_search_component(
    search_result=MyState.resources,
    selected_item=MyState.selected_resource,
    item_selected=MyState.select_item,
    search_trigger=MyState.search,
    placeholder="Click to search...",
    min_input_search_length=1,  # Trigger search after 1 character
    init_search_on_focus=True,  # Search immediately on focus
    page_size=10,               # 10 items per page
)"""

    return page_layout(
        "Input Search Component",
        "This page demonstrates the input search component for searching and selecting items with autocomplete functionality.",
        # Basic input search example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="input_search_component",
            description="A searchable input field with autocomplete functionality. "
            "It triggers search requests as the user types and displays results in a dropdown.",
            func=input_search_component,
        ),
        # Custom configuration example
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="Custom Configuration",
            description="Customize the search behavior with parameters like min_input_search_length, "
            "init_search_on_focus, and page_size.",
            func=input_search_component,
        ),
    )

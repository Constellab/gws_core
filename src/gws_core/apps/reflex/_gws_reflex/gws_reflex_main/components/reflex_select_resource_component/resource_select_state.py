"""State management for resource selection dialog with search filters."""

from abc import abstractmethod

import reflex as rx

from gws_core.core.classes.paginator import Paginator
from gws_core.core.utils.logger import Logger
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder


class ResourceSelectState(rx.State, mixin=True):
    """State management for resource search and selection.

    This state class manages the resource search dialog with filters
    for name, flagged status, and archived status. It displays search
    results in a table format.
    """

    # Dialog state
    dialog_opened: bool = False

    # Filter state
    name_filter: str = ""
    include_not_flagged: bool = False  # If False: only flagged resources, If True: no filter
    include_archived: bool = False  # If False: only not archived, If True: no filter

    # Pagination state
    current_page: int = 0
    items_per_page: int = 20
    has_more_pages: bool = True
    total_items: int = 0

    # Search results
    resources: list[ResourceModelDTO] = []
    is_loading: bool = False
    is_loading_more: bool = False

    # Private list of resource models (not converted to DTO)
    _resource_models: list[ResourceModel] = []

    # Selected resource
    selected_resource_id: str | None = None

    @rx.event(background=True)
    async def open_dialog(self):
        """Open the resource selection dialog and trigger initial search."""
        async with self:
            self.dialog_opened = True
            self.is_loading = True
            self.current_page = 0
            self.resources = []
            self._resource_models = []

        await self._load_page(0)

        async with self:
            self.is_loading = False

    @rx.event
    def close_dialog(self):
        """Close the dialog and reset filters."""
        self.dialog_opened = False
        self._reset_filters()

    def _reset_filters(self):
        """Reset all filter values."""
        self.name_filter = ""
        self.include_not_flagged = False
        self.include_archived = False
        self.resources = []
        self._resource_models = []
        self.selected_resource_id = None
        self.current_page = 0
        self.has_more_pages = True
        self.total_items = 0

    @rx.event(background=True)
    async def search_resources(self, form_data: dict):
        """Search for resources based on current filters (resets to page 0)."""
        async with self:
            self.is_loading = True
            self.current_page = 0
            self.resources = []
            self._resource_models = []
            # Update filter state from form data
            # Checkboxes return "on" when checked, or are not present when unchecked
            self.name_filter = form_data.get("name_filter", "")
            self.include_not_flagged = form_data.get("include_not_flagged") == "on"
            self.include_archived = form_data.get("include_archived") == "on"

        await self._load_page(0)

        async with self:
            self.is_loading = False

    @rx.event(background=True)
    async def load_more_resources(self):
        """Load the next page of resources for infinite scroll."""
        if not self.has_more_pages or self.is_loading_more:
            return

        async with self:
            self.is_loading_more = True
            next_page = self.current_page + 1

        await self._load_page(next_page)

        async with self:
            self.is_loading_more = False

    async def _load_page(self, page: int):
        """Load a specific page of resources."""
        try:
            # Build search query using ResourceSearchBuilder
            search_builder = await self.create_search_builder()

            # Execute paginated search
            paginator: Paginator[ResourceModel] = search_builder.search_page(
                page=page, number_of_items_per_page=self.items_per_page
            )

            # Store resource models and convert to DTOs
            new_resource_models = list(paginator.results)
            new_resources = [resource.to_dto() for resource in new_resource_models]

            # Update state
            async with self:
                if page == 0:
                    self._resource_models = new_resource_models
                    self.resources = new_resources
                else:
                    self._resource_models = self._resource_models + new_resource_models
                    self.resources = self.resources + new_resources

                self.current_page = page
                self.has_more_pages = not paginator.page_info.is_last_page
                self.total_items = paginator.page_info.total_number_of_items

        except Exception as e:
            Logger.error(f"Failed to load resources page {page}: {e}")
            async with self:
                if page == 0:
                    self.resources = []
                    self._resource_models = []
                self.has_more_pages = False

    @rx.event
    async def select_resource(self, resource_id: str):
        """Select a resource from the search results.

        This method can be extended/overridden in substates to handle custom logic.
        """
        self.selected_resource_id = resource_id

        # find the full ResourceModel from the private list
        resource_model = next((res for res in self._resource_models if res.id == resource_id), None)
        if resource_model is None:
            raise Exception("Selected resource model not found")
        result = await self.on_resource_selected(resource_model)
        self.close_dialog()
        return result

    async def create_search_builder(self) -> ResourceSearchBuilder:
        """
        Create a ResourceSearchBuilder with current filters applied.

        Can be overridden by subclasses to add additional filters.

        Example:
            ```python
            class MyResourceSelectState(ResourceSelectState):
                async def create_search_builder(self) -> ResourceSearchBuilder:
                    search_builder = await super().create_search_builder()
                    # Add custom filter to only include resources of a specific type
                    search_builder.add_resource_types_and_sub_types_filter([MyResourceType])
                    return search_builder
            ```
        """
        search_builder = ResourceSearchBuilder()

        # Apply name filter if set
        if self.name_filter and self.name_filter.strip():
            search_builder.add_name_filter(self.name_filter.strip())

        # Apply flagged filter: if not including not-flagged, only show flagged resources
        if not self.include_not_flagged:
            search_builder.add_flagged_filter(True)

        # Apply archived filter: if not including archived, only show not-archived resources
        if not self.include_archived:
            search_builder.add_is_archived_filter(False)

        return search_builder

    @abstractmethod
    async def on_resource_selected(self, resource_model: ResourceModel):
        """Abstract method to handle resource selection.

        Must be implemented by subclasses to define custom behavior
        when a resource is selected.
        """
        pass

from typing import Any, Generic, TypeVar

import reflex as rx
from reflex.vars import Var

from gws_core.core.model.model_dto import BaseModelDTO, PageDTO

asset_path = rx.asset("reflex_input_search_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path

InputSearchResultObjectType = TypeVar("InputSearchResultObjectType", bound=BaseModelDTO)


class InputSearchResultDTO(BaseModelDTO, Generic[InputSearchResultObjectType]):
    """DTO representing a single search result item.

    :param id: Unique identifier for the item
    :type id: str
    :param display_text: Text to display in the search results dropdown
    :type display_text: str
    :param object: The actual object associated with the search result item.
        This is the object that will be returned when the item is selected.
    :type object: InputSearchResultObjectType
    """

    id: str
    display_text: str
    object: InputSearchResultObjectType

    @staticmethod
    def from_json_object(
        data: dict, object_type: type[InputSearchResultObjectType]
    ) -> "InputSearchResultDTO[InputSearchResultObjectType]":
        """Create an InputSearchResultDTO from a JSON dictionary.

        :param data: The JSON dictionary representing the search result item
        :type data: dict
        :param object_type: The type of the object contained in the search result
        :type object_type: type[InputSearchResultObjectType]
        :return: An instance of InputSearchResultDTO
        :rtype: InputSearchResultDTO[InputSearchResultObjectType]
        """
        return InputSearchResultDTO(
            id=data["id"],
            display_text=data["display_text"],
            object=object_type.from_json(data["object"]),
        )


class InputSearchComponent(rx.Component):
    """Input Search component using dc-input-search web component.

    This component provides a searchable input field with autocomplete functionality.
    It triggers search requests as the user types and displays results in a dropdown.
    """

    library = public_js_path
    tag = "InputSearchComponent"

    search_result: Var[PageDTO | None]
    """The paginated search results to display in the dropdown."""

    selected_item: Var[Any | None]
    """The currently selected item."""

    placeholder: Var[str | None]
    """Optional placeholder text displayed in the input field when empty."""

    required: Var[bool | None]
    """Optional flag indicating whether the input is required."""

    min_input_search_length: Var[int]
    """Minimum number of characters required to trigger a search. Defaults to 2."""

    init_search_on_focus: Var[bool]
    """If True, triggers an initial search when the input receives focus. Defaults to False."""

    page_size: Var[int]
    """Number of items per page in the search results. Defaults to 20."""

    disabled: Var[bool]
    """If True, disables the input field. Defaults to False."""

    item_selected: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    """Event handler called when an item is selected from the search results."""

    search_trigger: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    """Event handler called when a search should be performed."""


def input_search_component(
    search_result: Var[PageDTO[InputSearchResultDTO] | None],
    selected_item: Var[Any | None],
    item_selected: rx.EventHandler[rx.event.passthrough_event_spec(dict)],
    search_trigger: rx.EventHandler[rx.event.passthrough_event_spec(dict)],
    placeholder: str | None = None,
    required: bool | None = None,
    min_input_search_length: int = 2,
    init_search_on_focus: bool = False,
    page_size: int = 20,
    disabled: bool = False,
    **kwargs,
):
    """Create an InputSearchComponent with the given configuration.

    This component provides a searchable input field with autocomplete functionality.
    It triggers search requests as the user types and displays results in a dropdown.

    :param search_result: The paginated search results to display in the dropdown.
        Should be a PageDTO containing InputSearchResultDTO items.
    :type search_result: Var[PageDTO[InputSearchResultDTO] | None]
    :param selected_item: The currently selected item. Can be used to pre-populate
        the input with a selected value.
    :type selected_item: Var[Any | None]
    :param item_selected: Event handler called when an item is selected from the
        search results. Receives the selected InputSearchResultDTO as a dictionary.
    :type item_selected: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    :param search_trigger: Event handler called when a search should be performed.
        Receives a dictionary with 'search' (str) and pagination info.
    :type search_trigger: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    :param placeholder: Optional placeholder text for the input field, defaults to None
    :type placeholder: Optional[str], optional
    :param required: Optional flag to mark the input as required, defaults to None
    :type required: Optional[bool], optional
    :param min_input_search_length: Minimum number of characters required to trigger
        a search, defaults to 2
    :type min_input_search_length: int, optional
    :param init_search_on_focus: If True, triggers an initial search when the input
        receives focus, defaults to False
    :type init_search_on_focus: bool, optional
    :param page_size: Number of items per page in the search results, defaults to 20
    :type page_size: int, optional
    :param disabled: If True, disables the input field, defaults to False
    :type disabled: bool, optional
    :return: An InputSearchComponent instance
    :rtype: InputSearchComponent

    **Example usage**::

        from gws_reflex_main.gws_components import input_search_component, InputSearchResultDTO
        from gws_core.core.model.model_dto import PageDTO

        class MyState(rx.State):
            _search_results: PageDTO[InputSearchResultDTO] | None = None
            _selected_item: InputSearchResultDTO | None = None

            @rx.var
            def search_results(self) -> PageDTO[InputSearchResultDTO] | None:
                return self._search_results

            @rx.var
            def selected_item(self) -> InputSearchResultDTO | None:
                return self._selected_item

            @rx.event
            async def handle_search(self, event_data: dict):
                search_text = event_data.get("search", "")
                # Perform search and update self._search_results
                ...

            @rx.event
            def handle_item_selected(self, event_data: dict):
                self._selected_item = InputSearchResultDTO(**event_data)

        input_search_component(
            search_result=MyState.search_results,
            selected_item=MyState.selected_item,
            item_selected=MyState.handle_item_selected,
            search_trigger=MyState.handle_search,
            placeholder="Search for items...",
            min_input_search_length=2,
        )
    """
    return InputSearchComponent.create(
        search_result=search_result,
        selected_item=selected_item,
        item_selected=item_selected,
        search_trigger=search_trigger,
        placeholder=placeholder,
        required=required,
        min_input_search_length=min_input_search_length,
        init_search_on_focus=init_search_on_focus,
        page_size=page_size,
        disabled=disabled,
        **kwargs,
    )

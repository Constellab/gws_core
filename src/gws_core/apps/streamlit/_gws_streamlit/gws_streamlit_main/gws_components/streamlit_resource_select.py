from typing import Any

import streamlit as st

from gws_core.resource.resource_model import ResourceModel

from ..gws_streamlit_main_state import StreamlitMainState
from .streamlit_gws_component_loader import StreamlitComponentLoader


class StreamlitResourceSelect:
    """Streamlit component to select a resource.

    This component is a wrapper around the GWS resource search component.
    It allows the user to search and select a resource.
    """

    _streamlit_component_loader = StreamlitComponentLoader("select-resource")
    # Dictionary to set default filters
    filters: dict[str, Any] = {}
    # Dictionary to track which filters are disabled
    disabled_filters: dict[str, bool] = {}

    def __init__(self):
        """Initialize the StreamlitResourceSelect component."""
        self.filters = {}
        self.disabled_filters = {}

    def set_disabled_filters(self, disabled_filters: dict[str, bool]) -> None:
        """Set the disabled filters for the resource search.

        :param disabled_filters: Dictionary of filter keys and their disabled status
        :type disabled_filters: dict[str, bool]
        """
        self.disabled_filters = disabled_filters

    def set_filters(self, filters: dict[str, Any]) -> None:
        """Set the filters for the resource search.

        :param filters: Dictionary of filters to apply
        :type filters: dict[str, Any]
        """
        self.filters = filters

    def add_filter(self, key: str, value: Any, disabled: bool = False) -> None:
        """Set a filter for the resource search.

        :param key: Filter key
        :type key: str
        :param value: Filter value
        :type value: Any
        """
        self.filters[key] = value
        self.disabled_filters[key] = disabled

    def add_tag_filter(self, key: str, value: Any = None, disabled: bool = False) -> None:
        """Add a tag filter to the resource search.

        :param key: Tag key to filter by
        :type key: str
        :param value: Optional tag value to filter by, defaults to None
        :type value: Any, optional
        """
        if "tags" not in self.filters:
            self.filters["tags"] = []
        tag = {"key": key, "value": value} if value is not None else {"key": key}
        self.filters["tags"].append(tag)
        self.disabled_filters["tags"] = disabled

    def add_column_tag_filter(self, key: str, value: Any = None, disabled: bool = False) -> None:
        """Add a column tag filter to the resource search.

        :param key: Column tag filter key to add
        :type key: str

        :param value: Optional column tag filter value to add, defaults to None
        :type value: Any, optional
        """
        if "columnTags" not in self.filters:
            self.filters["columnTags"] = []
        tag = {"key": key, "value": value} if value is not None else {"key": key}
        self.filters["columnTags"].append(tag)
        self.disabled_filters["columnTags"] = disabled

    def set_resource_typing_names_filter(
        self, resource_typing_names: list[str], disabled: bool = False
    ) -> None:
        """Add a resource typing filter to the resource search.

        :param resource_typing_names: List of resource typing names to filter by
        :type resource_typing_names: list[str]
        """
        self.filters["resourceTypingNames"] = resource_typing_names
        self.disabled_filters["resourceTypingNames"] = disabled

    def include_not_flagged_resources(self) -> None:
        """Add a filter to include not flagged resources."""
        self.filters["includeNotFlagged"] = True

    def select_resource(
        self,
        placeholder: str = "Search for resource",
        key="resource-select",
        default_resource: ResourceModel | None = None,
    ) -> ResourceModel | None:
        """Create a search box to select a resource.

        :param placeholder: Placeholder text shown within the component for empty searches, defaults to 'Search for resource'
        :type placeholder: str, optional
        :param key: Unique key for the component, defaults to 'resource-select'
        :type key: str, optional
        :param default_resource: Default resource to show, defaults to None
        :type default_resource: ResourceModel | None, optional
        :return: Selected resource model or None if no resource is selected
        :rtype: Optional[ResourceModel]
        """

        data = {
            "default_resource": default_resource.to_dto() if default_resource is not None else None,
            "placeholder": placeholder,
            "default_filters": self.filters,
            "disabled_filters": self.disabled_filters,
        }

        component_value = self._streamlit_component_loader.call_component(
            data, key=key, authentication_info=StreamlitMainState.get_user_auth_info()
        )

        key = f"__{key}_gws_resource_model__"

        if component_value is None:
            if default_resource is not None:
                st.session_state[key] = default_resource
                return default_resource
            st.session_state[key] = None
            return None

        if "resourceId" in component_value:
            resource_id = component_value["resourceId"]
            if resource_id is None:
                st.session_state[key] = None
                return None
            resource_model = ResourceModel.get_by_id_and_check(resource_id)

            st.session_state[key] = resource_model

        return st.session_state.get(key)

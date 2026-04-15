from typing import Any


class ResourceFrontSearchFilters:
    """Holds front-end search filter configuration for resource selection components.

    This class centralizes the filter logic shared between front-end resource
    selection components (Streamlit and Reflex) so both use the same API to
    configure default filters and disabled filters sent to the DC web component.

    :ivar filters: Dictionary of default filter values to apply to the resource search.
    :vartype filters: dict[str, Any]
    :ivar disabled_filters: Dictionary tracking which filters are disabled (the user
        cannot change them in the UI).
    :vartype disabled_filters: dict[str, bool]
    """

    filters: dict[str, Any]
    disabled_filters: dict[str, bool]

    def __init__(self) -> None:
        """Initialize an empty set of filters."""
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
        :param disabled: Whether the filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters[key] = value
        self.disabled_filters[key] = disabled

    def add_tag_filter(self, key: str, value: Any = None, disabled: bool = False) -> None:
        """Add a tag filter to the resource search.

        :param key: Tag key to filter by
        :type key: str
        :param value: Optional tag value to filter by, defaults to None
        :type value: Any, optional
        :param disabled: Whether the tags filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
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
        :param disabled: Whether the columnTags filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
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
        :param disabled: Whether the resourceTypingNames filter is disabled in the UI,
            defaults to False
        :type disabled: bool, optional
        """
        self.filters["resourceTypingNames"] = resource_typing_names
        self.disabled_filters["resourceTypingNames"] = disabled

    def include_not_flagged_resources(self) -> None:
        """Add a filter to include not flagged resources."""
        self.filters["includeNotFlagged"] = True

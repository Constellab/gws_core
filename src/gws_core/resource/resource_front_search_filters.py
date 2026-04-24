from datetime import datetime
from typing import Any


class ResourceFrontSearchFilters:
    """Holds front-end search filter configuration for resource selection components.

    This class centralizes the filter logic shared between front-end resource
    selection components (Streamlit and Reflex) so both use the same API to
    configure default filters and disabled filters sent to the DC web component.

    Filters mirror the ``LiResourceSearchFields`` TypeScript class used by the
    front-end and keep the same camelCase keys.

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

    def set_resource_typing_name_filter(
        self, resource_typing_name: str, disabled: bool = False
    ) -> None:
        """Set the single resource typing filter (matches ``resourceTypingName``).

        :param resource_typing_name: The resource typing name to filter by
        :type resource_typing_name: str
        :param disabled: Whether the filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["resourceTypingName"] = {"typingName": resource_typing_name}
        self.disabled_filters["resourceTypingName"] = disabled

    def set_resource_typing_names_filter(
        self, resource_typing_names: list[str], disabled: bool = False
    ) -> None:
        """Set the resource typing names filter (matches ``resourceTypingNames``).

        :param resource_typing_names: List of resource typing names to filter by
        :type resource_typing_names: list[str]
        :param disabled: Whether the resourceTypingNames filter is disabled in the UI,
            defaults to False
        :type disabled: bool, optional
        """
        self.filters["resourceTypingNames"] = resource_typing_names
        self.disabled_filters["resourceTypingNames"] = disabled

    def set_name_filter(self, name: str, disabled: bool = False) -> None:
        """Set the name filter (matches ``name``).

        :param name: Name substring to filter resources by
        :type name: str
        :param disabled: Whether the name filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["name"] = name
        self.disabled_filters["name"] = disabled

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

    def set_origin_filter(self, origin: str, disabled: bool = False) -> None:
        """Set the origin filter (matches ``origin``).

        :param origin: Resource origin identifier
        :type origin: str
        :param disabled: Whether the origin filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["origin"] = origin
        self.disabled_filters["origin"] = disabled

    def set_data_filter(self, data: str, disabled: bool = False) -> None:
        """Set the data filter (matches ``data``).

        :param data: Data substring to filter resources by
        :type data: str
        :param disabled: Whether the data filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["data"] = data
        self.disabled_filters["data"] = disabled

    def set_scenario_filter(self, scenario_id: str, disabled: bool = False) -> None:
        """Set the scenario filter (matches ``scenario``).

        :param scenario_id: Identifier of the scenario to filter resources by
        :type scenario_id: str
        :param disabled: Whether the scenario filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["scenario"] = {"id": scenario_id}
        self.disabled_filters["scenario"] = disabled

    def set_created_at_filter(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        disabled: bool = False,
    ) -> None:
        """Set the createdAt date interval filter (matches ``createdAt``).

        :param date_from: Optional lower bound of the creation date, defaults to None
        :type date_from: datetime | None, optional
        :param date_to: Optional upper bound of the creation date, defaults to None
        :type date_to: datetime | None, optional
        :param disabled: Whether the createdAt filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        interval: dict[str, Any] = {}
        if date_from is not None:
            interval["dateFrom"] = date_from.isoformat()
        if date_to is not None:
            interval["dateTo"] = date_to.isoformat()
        self.filters["createdAt"] = interval
        self.disabled_filters["createdAt"] = disabled

    def set_created_by_filter(self, user_id: str, disabled: bool = False) -> None:
        """Set the createdBy user filter (matches ``createdBy``).

        :param user_id: Identifier of the user who created the resource
        :type user_id: str
        :param disabled: Whether the createdBy filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["createdBy"] = {"id": user_id}
        self.disabled_filters["createdBy"] = disabled

    def set_folder_filter(self, folder_ids: list[str], disabled: bool = False) -> None:
        """Set the folder filter (matches ``folder``).

        :param folder_ids: List of folder identifiers to filter resources by
        :type folder_ids: list[str]
        :param disabled: Whether the folder filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["folder"] = [{"id": folder_id} for folder_id in folder_ids]
        self.disabled_filters["folder"] = disabled

    def set_is_archived_filter(self, is_archived: bool, disabled: bool = False) -> None:
        """Set the isArchived flag filter (matches ``isArchived``).

        :param is_archived: Whether to include only archived resources
        :type is_archived: bool
        :param disabled: Whether the isArchived filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["isArchived"] = is_archived
        self.disabled_filters["isArchived"] = disabled

    def set_include_children_resource(
        self, include_children: bool, disabled: bool = False
    ) -> None:
        """Set the includeChildrenResource flag (matches ``includeChildrenResource``).

        :param include_children: Whether to include children resources in the search
        :type include_children: bool
        :param disabled: Whether the includeChildrenResource filter is disabled in the UI,
            defaults to False
        :type disabled: bool, optional
        """
        self.filters["includeChildrenResource"] = include_children
        self.disabled_filters["includeChildrenResource"] = disabled

    def include_not_flagged_resources(self, disabled: bool = False) -> None:
        """Add a filter to include not flagged resources (matches ``includeNotFlagged``).

        :param disabled: Whether the includeNotFlagged filter is disabled in the UI,
            defaults to False
        :type disabled: bool, optional
        """
        self.filters["includeNotFlagged"] = True
        self.disabled_filters["includeNotFlagged"] = disabled

    def set_generated_by_process_filter(
        self, process_typing_name: str, disabled: bool = False
    ) -> None:
        """Set the generatedByProcess filter (matches ``generatedByProcess``).

        :param process_typing_name: Typing name of the process that generated the resource
        :type process_typing_name: str
        :param disabled: Whether the generatedByProcess filter is disabled in the UI,
            defaults to False
        :type disabled: bool, optional
        """
        self.filters["generatedByProcess"] = {"typingName": process_typing_name}
        self.disabled_filters["generatedByProcess"] = disabled

    def add_column_tag_filter(self, key: str, value: Any = None, disabled: bool = False) -> None:
        """Add a column tag filter to the resource search (matches ``columnTags``).

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

    def set_id_filter(self, resource_id: str, disabled: bool = False) -> None:
        """Set the id filter (matches ``id``).

        :param resource_id: Identifier of the resource to filter by
        :type resource_id: str
        :param disabled: Whether the id filter is disabled in the UI, defaults to False
        :type disabled: bool, optional
        """
        self.filters["id"] = resource_id
        self.disabled_filters["id"] = disabled

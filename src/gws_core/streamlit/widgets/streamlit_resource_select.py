from typing import List, Optional, Type

from peewee import Expression
from streamlit_searchbox import st_searchbox

from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
from gws_core.tag.tag import Tag


class ResourceSearchInput():

    search_builder: ResourceSearchBuilder

    def __init__(self):
        self.search_builder = ResourceSearchBuilder()

    def select(self, placeholder: str = 'Search for resource') -> Optional[ResourceModel]:

        selected_resource: ResourceModel = st_searchbox(
            self._search_resources,
            key="resource_searchbox",
            placeholder=placeholder,
        )

        return selected_resource

    def add_resource_type_filter(self, resource_type: Type[Resource]) -> "ResourceSearchInput":
        """Filter the search query by a specific resource type
        """
        self.search_builder.add_resource_type_filter(resource_type)
        return self

    def add_resource_typing_name_filter(self, resource_typing_name: str) -> "ResourceSearchInput":
        """Filter the search query by a specific resource typing name
        """
        self.search_builder.add_resource_typing_name_filter(resource_typing_name)
        return self

    def add_tag_filter(self, tag: Tag) -> "ResourceSearchInput":
        """Filter the search query by a specific tag
        """
        self.search_builder.add_tag_filter(tag)
        return self

    def add_origin_filter(self, origin: ResourceOrigin) -> "ResourceSearchInput":
        """Filter the search query by a specific origin
        """
        self.search_builder.add_origin_filter(origin)
        return self

    def add_folder_filter(self, folder_id: str) -> "ResourceSearchInput":
        """Filter the search query by a specific folder
        """
        self.search_builder.add_folder_filter(folder_id)
        return self

    def add_flagged_filter(self, flagged: bool) -> "ResourceSearchInput":
        """Filter the search query by a specific flag
        """
        self.search_builder.add_flagged_filter(flagged)
        return self

    def add_parent_filter(self, parent_id: str) -> "ResourceSearchInput":
        """Filter the search query by a specific parent
        """
        self.search_builder.add_parent_filter(parent_id)
        return self

    def add_expression(self, expression: Expression) -> "ResourceSearchInput":
        """Add a peewee expression to the search query
        """
        self.search_builder.add_expression(expression)
        return self

    # function with list of labels
    def _search_resources(self, searchterm: str) -> List[ResourceModel]:
        self.search_builder.add_name_filter(searchterm)

        return list(self.search_builder.build_search())

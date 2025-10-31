
from datetime import datetime
from typing import List

from gws_core.core.classes.search_builder import SearchOperator, SearchParams
from gws_core.space.space_dto import SpaceHierarchyObjectType
from gws_core.tag.tag import Tag


class SpaceHierarchyObjectSearchParams(SearchParams):

    def add_object_type_filter(self, operator: SearchOperator, value: SpaceHierarchyObjectType) -> None:
        """Add a filter to search for specific object types (file or folder)"""
        self.add_filter_criteria('objectType', operator, value.value)

    def add_name_filter(self, operator: SearchOperator, name: str) -> None:
        """Add a filter to search for specific names"""
        self.add_filter_criteria('name', operator, name)

    def add_last_modified_at_filter(self, operator: SearchOperator, value: datetime) -> None:
        """Add a filter to search for specific last modified at"""
        self.add_filter_criteria('lastModifiedAt', operator, value)

    def add_user_filter(self, operator: SearchOperator, user_id: str) -> None:
        """Add a filter to search for specific user ID"""
        self.add_filter_criteria('user.id', operator, user_id)

    def add_parent_id_filter(self, operator: SearchOperator, parent_id: str) -> None:
        """Add a filter to search for specific parent ID"""
        self.add_filter_criteria('parent.id', operator, parent_id)

    def add_tag_filter(self, operator: SearchOperator, tag: Tag) -> None:
        """Add a filter to search for specific tag"""
        self.add_filter_criteria('tags', operator, {'key': tag.key, 'value': tag.value})

    def add_tags_filter(self, operator: SearchOperator, tags: List[Tag]) -> None:
        """Add a filter to search for specific tags"""
        self.add_filter_criteria('tags', operator, [{'key': tag.key, 'value': tag.value} for tag in tags])



from typing import Type

from peewee import Expression

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder
from gws_core.task.task_model import TaskModel

from ..core.classes.search_builder import SearchFilterCriteria
from .resource_model import ResourceModel


class ResourceSearchBuilder(EntityWithTagSearchBuilder):
    """Search build for the resource model

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ResourceModel, EntityType.RESOURCE,
                         default_orders=[ResourceModel.created_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_.key == 'resource_typing_name':
            return ResourceModel.get_by_types_and_sub_expression([filter_.value])
        elif filter_.key == 'resource_typing_names':
            return ResourceModel.get_by_types_and_sub_expression(filter_.value)
        elif filter_.key == 'generated_by_task':
            entity_alias: Type[TaskModel] = TaskModel.alias()

            self.add_join(entity_alias, on=((entity_alias.id == ResourceModel.task_model) &
                                            (entity_alias.process_typing_name == filter_.value)
                                            ))

            return None

        return super().convert_filter_to_expression(filter_)

    def add_name_filter(self, name: str) -> "ResourceSearchBuilder":
        """Filter the search query by a specific name
        """
        self.add_expression(ResourceModel.name.contains(name))
        return self

    def add_resource_type_filter(self, resource_type: Type[Resource]) -> "ResourceSearchBuilder":
        """Filter the search query by a specific resource type
        """
        self.add_resource_typing_name_filter(resource_type.get_typing_name())
        return self

    def add_resource_typing_name_filter(self, resource_typing_name: str) -> "ResourceSearchBuilder":
        """Filter the search query by a specific resource typing name
        """
        self.add_expression(ResourceModel.resource_typing_name == resource_typing_name)
        return self

    def add_origin_filter(self, origin: ResourceOrigin) -> "ResourceSearchBuilder":
        """Filter the search query by a specific origin
        """
        self.add_expression(ResourceModel.origin == origin)
        return self

    def add_folder_filter(self, folder_id: str) -> "ResourceSearchBuilder":
        """Filter the search query by a specific folder
        """
        self.add_expression(ResourceModel.folder == folder_id)
        return self

    def add_flagged_filter(self, flagged: bool) -> "ResourceSearchBuilder":
        """Filter the search query by a specific flag
        """
        self.add_expression(ResourceModel.flagged == flagged)
        return self

    def add_parent_filter(self, parent_id: str) -> "ResourceSearchBuilder":
        """Filter the search query by a specific parent
        """
        self.add_expression(ResourceModel.parent_resource_id == parent_id)
        return self

    def add_is_archived_filter(self, is_archived: bool) -> "ResourceSearchBuilder":
        """Filter the search query by a specific archived status
        """
        self.add_expression(ResourceModel.is_archived == is_archived)
        return self

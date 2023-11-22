# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import Expression

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from ..core.classes.search_builder import SearchFilterCriteria
from .resource_model import ResourceModel


class ResourceModelSearchBuilder(EntityWithTagSearchBuilder):
    """Search build for the resource model

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ResourceModel, EntityType.RESOURCE,
                         default_orders=[ResourceModel.created_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_['key'] == 'resource_typing_name':
            return ResourceModel.get_by_types_and_sub_expression([filter_['value']])
        elif filter_['key'] == 'resource_typing_names':
            return ResourceModel.get_by_types_and_sub_expression(filter_['value'])

        return super().convert_filter_to_expression(filter_)

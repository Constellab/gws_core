

from typing import List

from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.experiment.experiment import Experiment
from gws_core.resource.view.view_types import ViewType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .view_config import ViewConfig


class ViewConfigSearchBuilder(EntityWithTagSearchBuilder):
    """Search build for the view cofnig

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ViewConfig, EntityType.VIEW,
                         default_orders=[ViewConfig.last_modified_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_['key'] == 'include_not_favorite':
            return None
        elif filter_['key'] == 'project':
            # Handle the project filters, get all experiment of this project and filter by experiment
            experiments: List[Experiment] = list(Experiment.select().where(
                Experiment.project.in_(filter_['value'])))
            return ViewConfig.experiment.in_(experiments)
        elif filter_['key'] == 'view_type':
            # consider table and tabular the same
            if ViewType.TABLE.value == filter_['value']:
                filter_['value'] = [ViewType.TABLE.value, ViewType.TABULAR.value]
                filter_['operator'] = 'IN'
        return super().convert_filter_to_expression(filter_)

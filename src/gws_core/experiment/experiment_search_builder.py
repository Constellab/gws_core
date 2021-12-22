# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import Expression
from playhouse.mysql_ext import Match

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..tag.tag import TagHelper
from .experiment import Experiment


class ExperimentSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Experiment, default_order=[Experiment.last_modified_at.desc()])

    def get_filter_expression(self, filter: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter['key'] == 'tags':
            return TagHelper.get_search_tag_expression(filter['value'], Experiment.tags)
        elif filter['key'] == 'text':
            # on text key, full text search on title and description
            return Match((Experiment.title, Experiment.description), filter['value'], modifier='IN BOOLEAN MODE')

        return super().get_filter_expression(filter)

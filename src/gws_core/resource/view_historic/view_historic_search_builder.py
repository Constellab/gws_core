# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import Expression

from ...core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from .view_historic import ViewHistoric


class ViewHistoricSearchBuilder(SearchBuilder):
    """Search build for the view historic

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ViewHistoric, default_order=[ViewHistoric.created_at.desc()])

    def get_filter_expression(self, filter: SearchFilterCriteria) -> Expression:
        return super().get_filter_expression(filter)

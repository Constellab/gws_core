# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Generic, List, TypedDict, TypeVar

from peewee import ModelSelect

from ..model.model import Model
from .query import Query


class PaginatorDict(TypedDict):
    objects: List[dict]
    page: int
    prev_page: int
    next_page: int
    last_page: int
    total_number_of_items: int
    total_number_of_pages: int
    number_of_items_per_page: int
    is_first_page: bool
    is_last_page: bool


PaginatorType = TypeVar('PaginatorType', bound=Model)


class Paginator(Generic[PaginatorType]):
    """
    Paginator class

    :property number_of_items_per_page: The default number of items per page
    :type number_of_items_per_page: `int`
    """

    number_of_items_per_page = 20
    _max_number_of_items_per_page = 100

    def __init__(self, query: ModelSelect,
                 page: int = 0,
                 number_of_items_per_page: int = 20,
                 view_params: dict = None):

        page = int(page)
        number_of_items_per_page = min(
            Paginator._max_number_of_items_per_page, int(number_of_items_per_page))

        if not view_params:
            self.view_params = {}
        else:
            self.view_params = view_params

        self.query = query
        self.paginated_query = query.paginate(page, number_of_items_per_page)
        self.page = page
        self.number_of_items_per_page = number_of_items_per_page
        self.total_number_of_items = query.count()
        self.total_number_of_pages = int(self.total_number_of_items/self.number_of_items_per_page) + int(
            bool(self.total_number_of_items % self.number_of_items_per_page))
        self.last_page = self.total_number_of_pages - 1
        self.first_page = 0
        self.next_page = min(self.page + 1, self.last_page)
        self.prev_page = max(self.page - 1, self.first_page)

    def _get_paginated_info(self) -> PaginatorDict:
        return {
            'objects': None,
            'page': self.page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'total_number_of_items': self.total_number_of_items,
            'total_number_of_pages': self.total_number_of_pages,
            'number_of_items_per_page': self.number_of_items_per_page,
            'is_first_page': self.page == self.first_page,
            'is_last_page': self.page == self.last_page
        }

    def to_json(self, deep: bool = False) -> PaginatorDict:
        paginator_dict: PaginatorDict = self._get_paginated_info()
        paginator_dict['objects'] = Query.format(
            self.paginated_query,
            deep=deep,
            as_json=True
        )
        return paginator_dict

    def render(self, deep: bool = False) -> PaginatorDict:
        paginator_dict: PaginatorDict = self._get_paginated_info()
        paginator_dict['objects'] = Query.format(
            self.paginated_query,
            view_params=self.view_params,
            as_view=True,
            deep=deep
        ),
        return paginator_dict

    def current_items(self):
        """
        Returns the current items in the paginators
        """

        return self.paginated_query

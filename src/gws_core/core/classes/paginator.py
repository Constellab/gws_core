# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, Generic, List, TypedDict, TypeVar

from numpy.core.numeric import Infinity
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


class PageInfo():
    """Simple class ot provide page information based on page, number_of_items_per_page, total_number_of_items
      It calculate all page information
    """
    page: int
    prev_page: int
    next_page: int
    last_page: int
    total_number_of_items: int
    total_number_of_pages: int
    number_of_items_per_page: int
    is_first_page: bool
    is_last_page: bool
    from_index: int
    to_index: int

    def __init__(self, page: int, number_of_items_per_page: int, total_number_of_items: int,
                 nb_max_of_items_per_page: int = Infinity, first_page: int = 0) -> None:
        self.page = page
        self.number_of_items_per_page = min(nb_max_of_items_per_page, int(number_of_items_per_page))
        self.total_number_of_items = total_number_of_items

        self.total_number_of_pages = int(self.total_number_of_items/self.number_of_items_per_page) + int(
            bool(self.total_number_of_items % self.number_of_items_per_page))
        self.first_page = first_page
        self.last_page = max(first_page + self.total_number_of_pages - 1, self.first_page)
        self.next_page = min(self.page + 1, self.last_page)
        self.prev_page = max(self.page - 1, self.first_page)

        self.from_index = (page - first_page) * number_of_items_per_page
        self.to_index = self.from_index + number_of_items_per_page

    def to_json(self) -> Dict:
        return {
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


class Paginator(Generic[PaginatorType]):
    """
    Paginator class

    :property number_of_items_per_page: The default number of items per page
    :type number_of_items_per_page: `int`
    """

    page_info: PageInfo
    query: Query
    paginated_query: Any

    _MAX_NUMBER_OF_ITEMS_PER_PAGE = 100

    def __init__(self, query: ModelSelect,
                 page: int = 0,
                 number_of_items_per_page: int = 20,
                 view_params: dict = None):
        if not view_params:
            self.view_params = {}
        else:
            self.view_params = view_params

        self.query = query
        # add 1 to page because peewee starts with 1
        self.paginated_query = query.paginate(page + 1, number_of_items_per_page)
        self.page_info = PageInfo(
            int(page),
            number_of_items_per_page, query.count(),
            Paginator._MAX_NUMBER_OF_ITEMS_PER_PAGE)

    def _get_paginated_info(self) -> PaginatorDict:
        return {
            'objects': None,
            **self.page_info.to_json(),
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

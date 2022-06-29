# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Callable, Dict, Generic, List, TypedDict, TypeVar

from gws_core.core.classes.jsonable import ListJsonable
from numpy.core.numeric import Infinity
from peewee import ModelSelect

from ..model.model import Model


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
    from_index: int
    to_index: int

    # Only set to true when the page is filter manually after the request so the total count can be inexact
    total_is_approximate: bool = False

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

    @property
    def is_first_page(self) -> bool:
        return self.page <= self.first_page

    @property
    def is_last_page(self) -> bool:
        return self.page >= self.last_page

    def to_json(self) -> Dict:
        return {
            'page': self.page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'total_number_of_items': self.total_number_of_items,
            'total_number_of_pages': self.total_number_of_pages,
            'number_of_items_per_page': self.number_of_items_per_page,
            'is_first_page': self.is_first_page,
            'is_last_page': self.is_last_page,
            'total_is_approximate': self.total_is_approximate
        }


class Paginator(Generic[PaginatorType]):
    """
    Paginator class

    :property number_of_items_per_page: The default number of items per page
    :type number_of_items_per_page: `int`
    """

    page_info: PageInfo
    results: List[PaginatorType]

    _query: ModelSelect
    _nb_of_items_per_page: int
    _nb_max_of_items_per_page: int

    def __init__(self, query: ModelSelect,
                 page: int = 0,
                 nb_of_items_per_page: int = 20,
                 nb_max_of_items_per_page: int = 100,
                 view_params: dict = None):
        if not view_params:
            self.view_params = {}
        else:
            self.view_params = view_params

        self._query = query
        self._nb_of_items_per_page = nb_of_items_per_page
        self._nb_max_of_items_per_page = nb_max_of_items_per_page
        self._call_query(page)

    def _call_query(self, page: int) -> None:
        # add 1 to page because peewee starts with 1
        self.results = (self._query.paginate(page + 1, self._nb_of_items_per_page))
        self.page_info = PageInfo(
            int(page),
            self._nb_of_items_per_page, self._query.count(),
            self._nb_max_of_items_per_page)

    def filter(self, filter_: Callable[[PaginatorType], Any], min_nb_of_result: int = 0) -> None:
        """
        Filter the current items in the paginators, the total count become approximate

        :param filter: The filter to apply
        :type filter: `function`
        :param min_nb_of_result: If provided, the query will be called multiple time until the number of result is
                                  greater than this value.
        :type min_nb_of_result: `int`
        """

        new_result = list(filter(filter_, self.results))

        # if we don't have enough result, we call the query again until we have enough result
        while len(new_result) < min_nb_of_result and not self.page_info.is_last_page:
            self._call_query(self.page_info.next_page)
            new_result += list(filter(filter_, self.results))

        self.results = new_result

        # mark the total count as approximate
        self.page_info.total_is_approximate = True

    def to_json(self, deep: bool = False) -> PaginatorDict:
        return {
            "objects": ListJsonable(self.results).to_json(deep=deep),
            **self.page_info.to_json(),
        }

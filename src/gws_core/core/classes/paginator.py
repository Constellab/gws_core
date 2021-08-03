# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .query import Query


class Paginator:
    """
    Paginator class

    :property number_of_items_per_page: The default number of items per page
    :type number_of_items_per_page: `int`
    """

    number_of_items_per_page = 20
    _max_number_of_items_per_page = 100

    def __init__(self, query,
                 page: int = 1,
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
        self.number_of_items = query.count()
        self.total_number_of_pages = int(self.number_of_items/self.number_of_items_per_page) + int(
            bool(self.number_of_items % self.number_of_items_per_page))
        self.next_page = min(self.page + 1, self.total_number_of_pages)
        self.prev_page = max(self.page - 1, 1)
        self.last_page = self.total_number_of_pages
        self.first_page = 1

    def paginator_dict(self):
        return {
            'page': self.page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'number_of_items': self.number_of_items,
            'total_number_of_pages': self.total_number_of_pages,
            'number_of_items_per_page': self.number_of_items_per_page,
            'is_first_page': self.page == self.first_page or self.total_number_of_pages == 0,
            'is_last_page': self.page == self.total_number_of_pages or self.total_number_of_pages == 0
        }

    def to_json(self, shallow: bool = False):
        return {
            'data': Query.format(
                self.paginated_query,
                shallow=shallow,
                as_json=True
            ),
            'paginator': self.paginator_dict()
        }

    def render(self, shallow: bool = False):
        return {
            'data': Query.format(
                self.paginated_query,
                view_params=self.view_params,
                as_view=True,
                shallow=shallow
            ),
            'paginator': self.paginator_dict()
        }

    def current_items(self):
        """
        Returns the current items in the paginators
        """

        return self.paginated_query

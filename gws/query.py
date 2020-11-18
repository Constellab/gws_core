# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pydantic import create_model

class Query:

    @classmethod
    def to_list(cls, Q, return_format="json"):
        _list = []
        if return_format.lower() == "json":
            for o in Q:
                _list.append(o.as_json())
        else:
            for o in Q:
                _list.append(o)
        
        return _list

class Paginator:
    number_of_items_per_page = 20
    Q = None
    def __init__(self, query, page: int = 1, number_of_items_per_page: int = 20):
        page = int(page)
        number_of_items_per_page = int(number_of_items_per_page)

        self.Q = query.paginate(page, number_of_items_per_page)
        self.page = page
        self.number_of_items_per_page = number_of_items_per_page
        self.number_of_items = query.count()
        self.total_number_of_pages = int(self.number_of_items/self.number_of_items_per_page) + int(bool(self.number_of_items % self.number_of_items_per_page))
        self.next_page = max(self.page + 1,self.total_number_of_pages)
        self.prev_page = min(self.page - 1, 1)
        self.last_page = self.total_number_of_pages
        self.first_page = 1

    def as_json( self ):
        return {
            'results' : Query.to_list( self.Q ),
            'paginator': {
                'page': self.page,
                'prev_page': self.prev_page,
                'next_page': self.next_page,
                'last_page': self.last_page,
                'number_of_items': self.number_of_items,
                'total_number_of_pages': self.total_number_of_pages,
                'number_of_items_per_page': self.number_of_items_per_page,
                'is_first_page': self.page == self.first_page,
                'is_last_page': self.page == self.total_number_of_pages
            }
        }
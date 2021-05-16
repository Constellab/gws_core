# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

class Query:

    @classmethod
    def format(cls, Q, view_params: dict={}, shallow=False):
        _list = []
        from gws.model import ViewModel, Viewable
        
        if shallow:
            for o in Q:
                _list.append(o.to_json(shallow=True))
        else:
            for o in Q:
                if isinstance(o, ViewModel):
                    _list.append(o.to_json())
                elif isinstance(o, Viewable):
                    o = o.cast()
                    view_model = o.view(params=view_params)
                    _list.append(view_model.to_json())   
                    #_list.append(o.to_json())
                else:
                    _list.append(o.to_json())

        return _list

class Paginator:
    number_of_items_per_page = 20    
    def __init__(self, query, page: int = 1, number_of_items_per_page: int = 20, view_params: dict = {}):
        page = int(page)
        number_of_items_per_page = int(number_of_items_per_page)
        
        self.view_params = view_params
        
        self.query = query
        self.paginated_query = query.paginate(page, number_of_items_per_page)        
        self.page = page
        self.number_of_items_per_page = number_of_items_per_page
        self.number_of_items = query.count()
        self.total_number_of_pages = int(self.number_of_items/self.number_of_items_per_page) + int(bool(self.number_of_items % self.number_of_items_per_page))
        self.next_page = min(self.page + 1,self.total_number_of_pages)
        self.prev_page = max(self.page - 1, 1)
        self.last_page = self.total_number_of_pages
        self.first_page = 1
    
    def _paginator_dict(self):
        return {
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

    def as_model_list( self ):
        return {
            'data' : Query.format( self.paginated_query ),
            'paginator': self._paginator_dict()
        }

    def to_json( self, shallow=False ):
        return {
            'data' : Query.format( self.paginated_query, view_params=self.view_params, shallow=shallow ),
            'paginator': self._paginator_dict()
        }
    
    def current_items(self):
        """
        Returns the current items in the paginators
        """
        
        return self.paginated_query

# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from gws.query import Paginator
from gws.model import Config

from .base_service import BaseService

class ConfigService(BaseService):
    
    # -- F --
    
    @classmethod
    def fetch_config_list(cls, \
                          search_text="", \
                          page: int=1, \
                          number_of_items_per_page: int=20, \
                          as_json=False) -> (Paginator, List[Config], List[dict], ):
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)

        if search_text:
            query = Config.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = Config.select().order_by(Config.creation_datetime.desc())
            paginator = Paginator(
                query, 
                page=page, 
                number_of_items_per_page=number_of_items_per_page
            )
            
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator
    
    
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.model import Settings  
from gws.system import Monitor
from gws.http import *

from .base_service import BaseService

class LabService(BaseService):
    
    @classmethod
    def get_lab_monitor_data(cls, \
                             page: int=1, \
                             number_of_items_per_page: int=20, \
                             as_json: bool=False) -> (Paginator, dict, ):
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        Q = Monitor.select()
        P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return P.to_json()
        else:   
            return P
    
    
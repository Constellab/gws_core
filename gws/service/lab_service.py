# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.model import Settings  
from gws.http import *

from .base_service import BaseService

class SettingService(BaseService):
    
    @classmethod
    def get_lab_status(cls):
        return {}
    
    @classmethod
    def get_lab_monitor(cls, page=1, number_of_items_per_page=20):
        Q = Monitor.select()
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json()
    
    
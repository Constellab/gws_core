# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.model import Config

from .base_service import BaseService

class ConfigService(BaseService):
    _number_of_items_per_page = 50
    
    # -- F --
    
    @classmethod
    def fetch_config_list(cls, page=1, number_of_items_per_page=20, filters=[]):
        Q = Config.select()\
                        .order_by(Config.creation_datetime.desc())
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)
    
    
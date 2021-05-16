# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.model import Protocol, Experiment
from gws.http import *

from .base_service import BaseService

class ProtocolService(BaseService):
    
    # -- F --
    
    @classmethod
    def fetch_protocol(cls, uri=None):
        try:
            p = Protocol.get(Protocol.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"No protocol found with uri {uri}")
        return p.to_json()
    
    @classmethod
    def fetch_protocol_list(cls, experiment_uri=None, page=1, number_of_items_per_page=20):
        if experiment_uri:
            Q = Protocol.select_me()\
                        .join(Experiment, on=(Protocol.id == Experiment.protocol_id))\
                        .where(Experiment.uri == experiment_uri)
        else:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Protocol.select_me()\
                        .order_by(Protocol.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)
            
            
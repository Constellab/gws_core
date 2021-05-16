# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.typing import ResourceType
from gws.model import Resource, Experiment
from gws.http import *

from .base_service import BaseService

class ResourceService(BaseService):
    
    # -- F --
    
    @classmethod
    def fetch_resource_type_list(cls, page=1, number_of_items_per_page=20, filters=[]):
        Q = ResourceType.select()\
                        .order_by(ResourceType.rtype.desc())  
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)      
     
        
    @classmethod
    def fetch_resource_list(cls, resource_type="resource", experiment_uri=None, page=1, number_of_items_per_page=20):
        from gws.service.model_service import ModelService
        t = None
        if resource_type:
            t = ModelService.get_model_type(resource_type)
            if t is None:
                raise HTTPNotFound(detail=f"Resource type '{resource_type}' not found")
        else:
            t = Resource
            
        if experiment_uri: 
            Q = t.select() \
                 .join(Experiment) \
                 .where(Experiment.uri == experiment_uri) \
                 .order_by(t.creation_datetime.desc())
        else:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = t.select()\
                 .order_by(t.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)
    
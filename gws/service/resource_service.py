# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws.query import Paginator
from gws.typing import ResourceType
from gws.model import Resource, Experiment
from gws.http import *

from .base_service import BaseService

class ResourceService(BaseService):
    
    # -- F --
    
    @classmethod
    def fetch_resource(cls, \
                       type = "gws.model.Resource", \
                       uri: str = "") -> Resource:
        
        from gws.service.model_service import ModelService
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise HTTPNotFound(detail=f"Resource type '{type}' not found")
        else:
            t = Resource
            
        try:
            r = t.get(t.uri == uri)
            return r
        except Exception as err:
            raise HTTPNotFound(detail=f"No resource found with uri '{uri}' and type '{type}'", debug_error=err)
        
        
    @classmethod
    def fetch_resource_list(cls, \
                           type = "gws.model.Resource", \
                           search_text: str="", \
                           experiment_uri: str=None, \
                           page: int=1, number_of_items_per_page: int=20, \
                           as_json = False) -> (Paginator, List[Resource], List[dict], ):
        
        from gws.service.model_service import ModelService
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise HTTPNotFound(detail=f"Resource type '{type}' not found")
        else:
            t = Resource
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if search_text:
            Q = t.search(search_text)
            result = []
            for o in Q:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            
            P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': P._paginator_dict()
            }
        else:
            
            if t is Resource:
                Q = t.select().order_by(t.creation_datetime.desc())
            else:
                Q = t.select_me().order_by(t.creation_datetime.desc())
            
            if experiment_uri: 
                Q = Q.join(Experiment) \
                     .where(Experiment.uri == experiment_uri)
            
            P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
                
            if as_json:
                return P.to_json(shallow=True)
            else:
                return P

    
    @classmethod
    def fetch_resource_type_list(cls, \
                                 base_rtype: str=None, \
                                 page: int=1, \
                                 number_of_items_per_page :int=20, \
                                 as_json = False) -> (Paginator, dict):
        

        Q = ResourceType.select()\
                        .order_by(ResourceType.rtype.desc())  
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
        
        if as_json:
            return P.to_json(shallow=True)   
        else:
            return P
     
        
    
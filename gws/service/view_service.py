# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import glob
import os
import importlib
import inspect

from typing import List
from gws.base import DbManager
from gws.query import Paginator
from gws.model import Model, ViewModel, Process, Resource, Protocol, Experiment
from gws.settings import Settings
from gws.logger import Warning, Info, Error
from gws.http import *
from gws.dto.rendering_dto import RenderingDTO

from .base_service import BaseService
from .model_service import ModelService

class ViewService(BaseService):

    # -- A --
       
    @classmethod
    def fetch_view_model(cls, uri: str) -> ViewModel:
        
        """
        Fetch a view model

        :param uri: The uri of the ViewModel
        :type uri: `str`
        :return: A view model
        :rtype: `gws.model.ViewModel`
        """
        
        try:
            return ViewModel.get(ViewModel.uri == uri)
        except:
            raise HTTPNotFound(detail=f"ViewModel '{uri}' not found")
        
    @classmethod
    def fetch_list_of_view_models(cls, \
                                  search_text: str=None, \
                                  page: int=1, number_of_items_per_page:int =20, \
                                  as_json: bool=False) -> (List[ViewModel], List[dict], ):
        
        if search_text:
            Q = ViewModel.search(search_text)
            result = []
            for o in Q:
                if as_json:
                    result.append( o.get_related().to_json() )
                else:
                    result.append(o)
            
            P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': P._paginator_dict()
            }
        else:
            Q = ViewModel.select().order_by(ViewModel.creation_datetime.desc())
            P = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return P.to_json(shallow=True)
            else:
                return P
            
            
    # -- U --
    
    @classmethod
    def update_view_model(cls, uri: str, data: RenderingDTO) -> ViewModel:
        try:
            vm = ViewModel.get(ViewModel.uri == uri)
        except:
            raise HTTPNotFound(detail=f"ViewModel '{uri}' not found")
            
        vm.upate(data)
        return vm
    
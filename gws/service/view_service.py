# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from ..query import Paginator
from ..view_model import ViewModel
from ..http import *
from ..dto.rendering_dto import RenderingDTO
from .base_service import BaseService

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
        except Exception as err:
            raise HTTPNotFound(detail=f"ViewModel '{uri}' not found") from err
        
    @classmethod
    def fetch_list_of_view_models(cls, \
                                  search_text: str=None, \
                                  page: int=1, number_of_items_per_page:int =20, \
                                  as_json: bool=False) -> (List[ViewModel], List[dict], ):
        
        if search_text:
            query = ViewModel.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append( o.get_related().to_json() )
                else:
                    result.append(o)
            
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = ViewModel.select().order_by(ViewModel.creation_datetime.desc())
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator
            
    # -- U --
    
    @classmethod
    def update_view_model(cls, uri: str, data: RenderingDTO) -> ViewModel:
        try:
            view_model = ViewModel.get(ViewModel.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"ViewModel '{uri}' not found") from err
        view_model.upate(data)
        return view_model
    
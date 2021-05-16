# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
import importlib
import inspect
import asyncio

from gws.base import Base
from gws.logger import Error, Info
from gws.query import Query, Paginator
from gws.http import *

from typing import List
from fastapi import UploadFile, File as FastAPIFile



class Controller(Base):
    """
    Controller class
    """
    
    _settings = None

  
    @classmethod
    async def action(cls, action=None, object_type=None, object_uri=None, study_uri=None, data=None, page=1, number_of_items_per_page=20, filters="") -> 'ViewModel':
        """
        Process user actions

        :param action: The action
        :type action: str
        :param object_type: The type of the view model
        :type object_type: str
        :param object_uri: The uri of the view model
        :type object_uri: str
        :param data: The data
        :type data: dict
        :return: A view model corresponding to the action
        """
        
        from gws.service import ModelService
        try:
            if isinstance(data, str):
                if len(data) == 0:
                    data = {}
                else:
                    data = json.loads(data)
        except:
            raise Error("Controller", "action", "The data is not a valid JSON text")
        
        if action == "get":
            object_uris = object_uri.split(",")
            if len(object_uris) == 1 and not "all" in object_uris:
                model = cls.__action_get(object_type, object_uri, data)
            else:
                model = cls.__action_list(
                    object_type, object_uris, data=data, 
                    page=page, number_of_items_per_page=number_of_items_per_page
                )
        elif action == "update":
            # update objects
            model = ModelService.update(object_type, object_uri, data)
        elif action == "archive":
            model = ModelService.archive(True, object_type, object_uri)
        elif action == "unarchive":
            model = ModelService.unarchive(False, object_type, object_uri)
        elif action == "upload":
            model = await cls.__action_upload(data, study_uri=study_uri)
        elif action == "count":
            model = ModelService.count(object_type)
            
        return model

    # -- C --
    
    # -- I --
    
    
        
    # -- L --
    
    
    # -- M --
    
    # -- P --

    # -- R --
    
              
    # -- S --
        
        
    
    
    
    
    

    
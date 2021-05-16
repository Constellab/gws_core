# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app, ViewModelData

@core_app.get("/model/count/{object_type}", tags=["Models and ViewModels"])
async def count(object_type: str, \
                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get the count of objects of a given type
    
    - **object_type**: the object type
    """

    from gws.service.model_service import ModelService
    return ModelService.count_model( 
        object_type = object_type
    )

@core_app.post("/model/{object_type}/{object_uri}/archive", tags=["Models and ViewModels"])
async def archive_model(object_type: str, \
                             object_uri: str, \
                             _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive a ViewModel
    
    - **object_type**: the type of the object to archive.
    - **object_uri**: the uri of the object to archive
    """

    from gws.service.model_service import ModelService
    return ModelService.archive_model( 
        object_type = object_type, 
        object_uri = object_uri
    )

@core_app.post("/model/{object_type}/{object_uri}/unarchive", tags=["Models and ViewModels"])
async def unarchive_model(object_type: str, \
                          object_uri: str, \
                          _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive a ViewModel
    
    - **object_type**: the type of the object to archive.
    - **object_uri**: the uri of the object to archive
    """

    from gws.service.model_service import ModelService
    return ModelService.unarchive_model(
        object_type = object_type, 
        object_uri = object_uri
    )

@core_app.post("/view/{object_type}/{object_uri}/update", tags=["Models and ViewModels"])
async def update_view_model(object_type: str, \
                       object_uri: str, \
                       view_model: ViewModelData, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Update a ViewModel
    
    - **object_type**: the type of object of which the ViewModel is attached
    - **view_model**: data of the ViewModel `{uri: "uri_of_the_view_model", data: "parameters_of_the_view_model"}`
    """

    from gws.service.model_service import ModelService
    return ModelService.update_view_model( 
        object_type = object_type, 
        object_uri = object_uri, 
        data = view_model.params
    )

@core_app.get("/view/{object_type}/{object_uris}", tags=["Models and ViewModels"])
async def get_list_of_view_models(object_type: str, \
                         object_uris: Optional[str] = "all", \
                         page: int = 1, \
                         number_of_items_per_page: int = 20, \
                         filters: Optional[str] = "", \
                         view_params: Optional[str] = "{}", \
                        _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get a ViewModel
    
    Custom query params depending on the queryied model. 
    
    - **object_type**: the type of the object to fetch. Can be an existing ViewModel or a Viewable object with no ViewModel. In this case, default ViewModel is created and returned.
    - **object_uris**: the uris of the object to fetch. Use comma-separated values to fecth several uris or 'all' to fetch all the entries. When all entries are retrieve, the **filter** parameter can be used.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    - **filters**: filter to use to select data (**object_uris** must be equal to 'all'). The filter is matched (using full-text search) against to the `title` and the `description`.
    - **view_params**: key,value parameters of the ViewModel. The key,value specifications are given by the method `to_json()` of the corresponding object class. See class documentation.
    """
    
    from gws.service.model_service import ModelService
    
    try:
        params = json.loads(view_params)
    except:
        params = {}
    
    object_uris = object_uris.split(",")
    
    return ModelService.fetch_list_of_view_models( 
        object_type = object_type, 
        object_uris = object_uris, 
        data = params, 
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        filters = filters
    )


@core_app.get("/model/{object_type}/{object_uri}/verify", tags=["Models and ViewModels"])
async def verify_model_hash(object_type: str, \
                            object_uri: str, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Verify Model and ViewModel hash.
    
    Verify the integrity of a given object in the db to check if that object has been altered by any unofficial mean
    (e.g. manual changes of data in db, or partial changes without taking care of its dependency chain).
    
    Objects' integrity is based on an algorithm that computes hashes using objects' data and their dependency trees (like in block chain) rendering any data falsification difficult to hide.
    
    - **object_type**: the type of the object to delete.
    - **object_uri**: the uri of the object to delete
    """
    
    from gws.service.model_service import ModelService
    return ModelService.verify_model_hash(
        object_type=object_type, 
        object_uri=object_uri
    )

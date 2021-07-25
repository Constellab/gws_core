# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from fastapi import Depends
from ._auth_user import check_user_access_token
from .core_app import core_app

from ...exception.bad_request_exception import BadRequestException
from ...dto.user_dto import UserData
from ...dto.rendering_dto import RenderingDTO

@core_app.post("/view/{uri}/update", tags=["ViewModels"], summary="Update a view model")
async def update_a_view_model(uri: str, \
                      data: RenderingDTO, \
                      _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Update a ViewModel
    
    - **uri**: the uri of the ViewModel to update and render
    - **data**: the rendering data
    """

    from ...service.view_service import ViewService
    view_model = ViewService.update_view_model(
        uri = uri,
        data = data
    )
    try:
        return view_model.to_json()
    except Exception as err:
        raise BadRequestException(detail="Cannot render view.") from err

@core_app.get("/view/{uri}", tags=["ViewModels"], summary="Get a view model")
async def get_a_view_model(uri: str, \
                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get a ViewModel
        
    - **uri**: the uri of the ViewModel to fetch and render.
    """
    
    from ...service.view_service import ViewService
    view_model = ViewService.fetch_view_model(uri=uri)
    try:
        return view_model.to_json()
    except Exception as err:
        raise BadRequestException(detail="Cannot render view.") from err

@core_app.get("/view", tags=["ViewModels"], summary="Get the list of view models")
async def get_the_list_of_view_models(page: Optional[int] = 1, \
                                    number_of_items_per_page: Optional[int] = 20, \
                                    search_text: Optional[str] = "", \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get the list of ViewModel
    
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    - **search_text**: text used to filter the results. The test is matched (using full-text search) against to the `title` and the `description`. If the `search_text` is given, the parameter `model_type` is ignored.
    """
    
    from ...service.view_service import ViewService
    return ViewService.fetch_list_of_view_models(
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        search_text = search_text,
        as_json = True
    )

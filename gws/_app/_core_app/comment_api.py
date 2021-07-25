# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from fastapi import Depends

from ...dto.user_dto import UserData
from ...service.model_service import ModelService
from ...service.comment_service import CommentService
from ...dto.experiment_dto import ExperimentDTO
from ._auth_user import check_user_access_token
from .core_app import core_app

@core_app.post("/comment/{object_type}/{object_uri}/add", tags=["Comment"], summary="And new object comment")
async def add_object_comments(object_type: str, \
                            object_uri: str, \
                            message: str, \
                            reply_to_uri: str = None, \
                         _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Add a new comment
    
    - **object_type**: the type of the object to comment
    - **object_uri**: the uri of the object to comment
    - **message**: comment message
    - **reply_to_uri**: the uri of the comment to reply to
    """
    
    c = CommentService.add_comment(
        object_type=object_type, 
        object_uri=object_uri, 
        message=message, 
        reply_to_uri=reply_to_uri
    )
    return c.to_json()

@core_app.post("/comment/{object_type}/{object_uri}", tags=["Comment"], summary="Get the comments of an object")
async def get_object_comments(object_type: str, \
                            object_uri: str, \
                            page: int=1,
                            number_of_items_per_page=20,
                            _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Get object comments
    
    - **object_type**: the type of the object
    - **object_uri**: the uri of the object
    - **page**: the current page
    - **number_of_items_per_page**: the number of items per page (set equal to -1 to get all the comments)
    """
    
    return CommentService.fetch_object_comments(
        object_type=object_type,
        object_uri=object_uri,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
        as_json=True
    )
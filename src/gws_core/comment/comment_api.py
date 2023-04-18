# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from ..core_app import core_app
from ..user.auth_service import AuthService
from .comment_service import CommentService


@core_app.post("/comment/{object_typing_name}/{object_id}/add", tags=["Comment"], summary="And new object comment")
def add_object_comments(object_typing_name: str,
                        object_id: str,
                        message: str,
                        reply_to_id: str = None,
                        _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Add a new comment

    - **object_type**: the type of the object to comment
    - **object_id**: the id of the object to comment
    - **message**: comment message
    - **reply_to_id**: the id of the comment to reply to
    """

    c = CommentService.add_comment(
        object_typing_name=object_typing_name,
        object_id=object_id,
        message=message,
        reply_to_id=reply_to_id
    )
    return c.to_json()


@core_app.post("/comment/{object_typing_name}/{object_id}", tags=["Comment"], summary="Get the comments of an object")
def get_object_comments(object_typing_name: str,
                        object_id: str,
                        page: int = 0,
                        number_of_items_per_page=20,
                        _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Get object comments

    - **object_type**: the type of the object
    - **object_id**: the id of the object
    - **page**: the current page
    - **number_of_items_per_page**: the number of items per page (set equal to -1 to get all the comments)
    """

    return CommentService.get_object_comments(
        object_typing_name=object_typing_name,
        object_id=object_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()

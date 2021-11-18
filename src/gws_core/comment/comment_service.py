# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import NotFoundException
from ..core.model.model import Model
from ..core.service.base_service import BaseService
from .comment import Comment


class CommentService(BaseService):

    @classmethod
    def add_comment(cls, object_typing_name: str, object_uri: str, message: str, reply_to_uri: str = None) -> Comment:
        if reply_to_uri:
            try:
                parent = Comment.get(Comment.uri == reply_to_uri)
            except Exception as err:
                raise NotFoundException(
                    detail=f"The parent comment '{reply_to_uri}' not found") from err

            comment = Comment(
                object_uri=object_uri,
                object_typing_name=object_typing_name,
                reply_to=parent
            )
        else:
            comment = Comment(
                object_uri=object_uri,
                object_typing_name=object_typing_name,
            )

        comment.set_message(message)
        comment.save()
        return comment

    @classmethod
    def add_comment_to_model(cls, model: Model, message: str, reply_to_uri: str = None) -> Comment:
        return cls.add_comment(model._typing_name, model.uri, message, reply_to_uri)

    @classmethod
    def get_object_comments(cls,
                            object_typing_name: str,
                            object_uri: str,
                            page: int = 0,
                            number_of_items_per_page: int = 20) -> Paginator[Comment]:

        query = Comment.select()\
            .where((Comment.object_uri == object_uri) & (Comment.object_typing_name == object_typing_name))\
            .order_by(Comment.creation_datetime.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_model_comments(cls,
                           model: Model,
                           page: int = 0,
                           number_of_items_per_page: int = 20) -> Paginator[Comment]:

        return cls.get_object_comments(model._typing_name, model.uri, page, number_of_items_per_page)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import NotFoundException
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
    def fetch_object_comments(cls,
                              object_typing_name: str,
                              object_uri: str,
                              page: int = 1,
                              number_of_items_per_page: int = 20,
                              as_json=False) -> Union[List[Comment], List[dict]]:

        query = Comment.select()\
            .where((Comment.object_uri == object_uri) & (Comment.object_typing_name == object_typing_name))\
            .order_by(Comment.creation_datetime.desc())

        if number_of_items_per_page <= 0:
            if as_json:
                comments = []
                for c in query:
                    comments.append(c.to_json())
                return comments

            return query
        else:
            number_of_items_per_page = min(
                number_of_items_per_page, cls._number_of_items_per_page)
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)

            return paginator

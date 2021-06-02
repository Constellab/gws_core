# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from gws.query import Paginator
from gws.comment import Comment
from gws.http import HTTPNotFound
from .base_service import BaseService

class CommentService(BaseService):
    
    @classmethod
    def add_comment(cls, object_type: str, object_uri: str, text: str, reply_to_uri:str=None) -> Comment:
        if reply_to_uri:
            try:
                parent = Comment.get(Comment.uri == reply_to_uri)
            except Exception as err:
                raise HTTPNotFound(detail=f"The parent comment '{reply_to_uri}' not found") from err

            c = Comment(
                object_uri=object_uri,
                object_type=object_type,
                text=text, 
                reply_to=parent
            )
        else:
            c = Comment(
                object_uri=object_uri, 
                object_type=object_type,
                text=text
            )

        c.save()
        return c

    @classmethod
    def fetch_object_comments(cls, \
                            object_type: str, \
                            object_uri: str, \
                            page: int=1, \
                            number_of_items_per_page:int=20, \
                            as_json=False) -> (List[Comment], List[dict], ):

        query = Comment.select()\
                            .where((Comment.object_uri == object_uri) & (Comment.object_type == object_type))\
                            .order_by(Comment.creation_datetime.desc())

        if number_of_items_per_page <= 0:
            if as_json:
                comments = []
                for c in query:
                    comments.append(c.to_json())
                return comments
            else:
                return query
        else:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page )
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

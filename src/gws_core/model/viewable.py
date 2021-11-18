# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from ..comment.comment import Comment
from ..core.model.model import Model


class Viewable(Model):
    """
    Viewable class.
    """

    def add_comment(self, message: str, reply_to: Comment = None) -> Comment:
        """
        Add a new comment to this object

        :param message: The comment message
        :type message: `str`
        :param reply_to: The comment to reply to
        :type reply_to: `Comment`
        :returns: The added comment
        :rtype: `Comment`
        """

        if not self.id:
            self.save()

        comment: Comment = None
        if reply_to:
            comment = Comment(
                object_uri=self.uri,
                object_typing_name=self._typing_name,
                reply_to=reply_to
            )
        else:
            comment = Comment(
                object_typing_name=self._typing_name,
                object_uri=self.uri,
            )

        comment.set_message(message)
        comment.save()
        return comment

    @property
    def comments(self) -> List[Comment]:
        """
        Returns the list of comments of this object
        """

        return Comment.select()\
            .where(Comment.object_uri == self.uri)\
            .order_by(Comment.creation_datetime.desc())

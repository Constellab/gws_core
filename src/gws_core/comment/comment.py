# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import CharField, ForeignKeyField

from ..core.decorator.json_ignore import json_ignore
from ..core.model.model_with_user import ModelWithUser


@final
@json_ignore(["object_id", "object_typing_name"])
class Comment(ModelWithUser):
    """
    Comment class that represents generic object comments

    :property object_id: The id of the Viewable object to comment
    :type object_id: `str`
    :property object_typing_name: The type of the Viewable object to comment
    :type object_typing_name: `str`
    :property reply_to: The parent comment. It not `None` if this comment is the reply to another comment. It is `None` otherwise
    :type reply_to: `gws.comment.Comment`
    """

    object_id = CharField(null=False, index=True)
    # -> non-unique index (object_id, object_typing_name) is created in Meta
    object_typing_name = CharField(null=False)
    reply_to = ForeignKeyField('self', null=True, backref='+')
    _table_name = "gws_comment"

    # -- G --

    def get_message(self) -> str:
        return self.data["message"]

    # -- M --

    @property
    def message(self) -> str:
        return self.data["message"]

    # -- S --

    def set_message(self, msg: str):
        self.data["message"] = msg

    # -- T --

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the comment.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)
        _json["object"] = {
            "id": self.object_id,
            "type": self.object_typing_name
        }
        _json["reply_to"] = {
            "id": (self.reply_to.id if self.reply_to else "")}

        return _json

    class Meta:
        indexes = (
            # create a non-unique index on object_id, object_typing_name
            (('object_id', 'object_typing_name'), False),
        )

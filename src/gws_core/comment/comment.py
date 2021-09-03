# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import CharField, ForeignKeyField

from ..core.decorator.json_ignore import json_ignore
from ..core.model.model import Model
from ..model.typing_register_decorator import typing_registrator


@final
@json_ignore(["object_uri", "object_typing_name"])
@typing_registrator(unique_name="Comment", object_type="GWS_CORE", hide=True)
class Comment(Model):
    """
    Comment class that represents generic object comments

    :property object_uri: The uri of the Viewable object to comment
    :type object_uri: `str`
    :property object_typing_name: The type of the Viewable object to comment
    :type object_typing_name: `str`
    :property reply_to: The parent comment. It not `None` if this comment is the reply to another comment. It is `None` otherwise
    :type reply_to: `gws.comment.Comment`
    """

    object_uri = CharField(null=False, index=True)
    # -> non-unique index (object_uri, object_typing_name) is created in Meta
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
            "uri": self.object_uri,
            "type": self.object_typing_name
        }
        _json["reply_to"] = {
            "uri": (self.reply_to.uri if self.reply_to else "")}

        return _json

    class Meta:
        indexes = (
            # create a non-unique index on object_uri, object_typing_name
            (('object_uri', 'object_typing_name'), False),
        )

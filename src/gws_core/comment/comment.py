# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from peewee import CharField, ForeignKeyField

from ..core.model.model import Model


class Comment(Model):
    """
    Comment class that represents generic object comments

    :property object_uri: The uri of the Viewable object to comment
    :type object_uri: `str`
    :property object_type: The type of the Viewable object to comment
    :type object_type: `str`
    :property reply_to: The parent comment. It not `None` if this comment is the reply to another comment. It is `None` otherwise
    :type reply_to: `gws.comment.Comment`
    """

    object_uri = CharField(null=False, index=True)
    # -> non-unique index (object_uri, object_type) is created in Meta
    object_type = CharField(null=False)
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

    def to_json(self, *, shallow=False, stringify: bool = False, prettify: bool = False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the comment.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(shallow=shallow, **kwargs)
        _json["object"] = {
            "uri": self.object_uri,
            "type": self.object_type
        }
        _json["reply_to"] = {
            "uri": (self.reply_to.uri if self.reply_to else "")}

        del _json["object_uri"]
        del _json["object_type"]

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    class Meta:
        indexes = (
            # create a non-unique index on object_uri, object_type
            (('object_uri', 'object_type'), False),
        )
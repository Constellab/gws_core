# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from peewee import CharField, ForeignKeyField, IntegerField

from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.protocol.protocol_types import ProtocolConfigDict
from gws_core.tag.taggable_model import TaggableModel

from ..core.model.model_with_user import ModelWithUser


class ProtocolTemplate(ModelWithUser, TaggableModel):
    """ Entity to store template of protocol

    :param ModelWithUser: _description_
    :type ModelWithUser: _type_
    """

    name = CharField(max_length=255)

    # version number of the protocol template
    version = IntegerField(null=False, default=1)

    _table_name = "gws_protocol_template"

    def get_template(self) -> ProtocolConfigDict:
        return self.data

    def set_template(self, template: ProtocolConfigDict):
        self.data = template

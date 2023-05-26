# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from peewee import CharField, IntegerField

from gws_core.core.model.db_field import JSONField
from gws_core.process.process_factory import ProcessFactory
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_types import ProtocolConfigDict
from gws_core.tag.taggable_model import TaggableModel

from ..core.model.model_with_user import ModelWithUser


class ProtocolTemplate(ModelWithUser, TaggableModel):
    """ Entity to store template of protocol

    :param ModelWithUser: _description_
    :type ModelWithUser: _type_
    """

    name = CharField(max_length=255)

    description = JSONField(null=True)

    # version number of the protocol template
    version = IntegerField(null=False, default=1)

    _table_name = "gws_protocol_template"

    def get_template(self) -> ProtocolConfigDict:
        return self.data

    def set_template(self, template: ProtocolConfigDict):
        self.data = template

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        # create a new protocol to refresh the template info ()
        protocol_model = ProcessFactory.create_protocol_model_from_graph(self.get_template())
        return protocol_model.dumps_graph('config')

    @classmethod
    def from_protocol_model(
            cls, protocol_model: ProtocolModel, name: str, description: str = None) -> 'ProtocolTemplate':
        protocol_template = ProtocolTemplate()
        protocol_template.set_template(protocol_model.dumps_graph('config'))
        protocol_template.name = name
        protocol_template.description = description
        return protocol_template

    @classmethod
    def from_json(cls, json_: dict) -> 'ProtocolTemplate':
        protocol_template = ProtocolTemplate()
        protocol_template.name = json_['name']
        protocol_template.description = json_.get('description')
        protocol_template.version = json_.get('version')
        protocol_template.set_template(json_['data'])

        return protocol_template

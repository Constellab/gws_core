
from typing import Any, Dict

from peewee import CharField, IntegerField

from gws_core.core.model.db_field import JSONField
from gws_core.impl.rich_text.rich_text_field import RichTextField
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph_factory import \
    ProtocolGraphFactoryFromType
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_template.scenario_template_dto import (
    ScenarioTemplateDTO, ScenarioTemplateExportDTO)

from ..core.model.model_with_user import ModelWithUser


class ScenarioTemplate(ModelWithUser):
    """ Entity to store template of protocol

    :param ModelWithUser: _description_
    :type ModelWithUser: _type_
    """

    CURRENT_VERSION = 3

    name = CharField(max_length=255)

    description = RichTextField(null=True)

    # version number of the scenario template
    version = IntegerField(null=False, default=1)
    data: Dict[str, Any] = JSONField(null=True)

    _table_name = "gws_scenario_template"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved() and not self.data:
            self.data = {}

    def get_template(self) -> ProtocolGraphConfigDTO:
        return ProtocolGraphConfigDTO.from_json(self.data)

    def set_template(self, template: ProtocolGraphConfigDTO):
        self.data = template.to_json_dict()

    def to_dto(self) -> ScenarioTemplateDTO:
        return ScenarioTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            version=self.version,
            description=self.description
        )

    def to_export_dto(self) -> ScenarioTemplateExportDTO:
        # create a new protocol to refresh the template info ()
        return ScenarioTemplateExportDTO(
            id=self.id,
            name=self.name,
            version=self.version,
            data=self.get_protocol_config_dto(),
            description=self.description
        )

    def get_protocol_config_dto(self) -> ProtocolGraphConfigDTO:
        protocol_model = self.generate_protocol_model()
        return protocol_model.to_protocol_config_dto()

    def generate_protocol_model(self) -> ProtocolModel:
        factory = ProtocolGraphFactoryFromType(self.get_template())
        protocol_model: ProtocolModel = factory.create_protocol_model()

        protocol_model.name = self.name

        return protocol_model

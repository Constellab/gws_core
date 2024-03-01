# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Any, Dict

from peewee import CharField, IntegerField
from pydantic import StrBytes

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.db_field import JSONField
from gws_core.core.utils.logger import Logger
from gws_core.process.process_factory import ProcessFactory
from gws_core.protocol.protocol_dto import ProtocolConfigDTO
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol_template.protocol_template_dto import (
    ProtocolTemplateDTO, ProtocolTemplateExportDTO)
from gws_core.tag.taggable_model import TaggableModel

from ..core.model.model_with_user import ModelWithUser


class ProtocolTemplate(ModelWithUser, TaggableModel):
    """ Entity to store template of protocol

    :param ModelWithUser: _description_
    :type ModelWithUser: _type_
    """

    name = CharField(max_length=255)

    description = JSONField(null=True)
    old_description = JSONField(null=True)

    # version number of the protocol template
    version = IntegerField(null=False, default=1)
    data: Dict[str, Any] = JSONField(null=True)

    _table_name = "gws_protocol_template"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved() and not self.data:
            self.data = {}

    def get_template(self) -> ProtocolConfigDTO:
        return ProtocolConfigDTO.from_json(self.data)

    def set_template(self, template: ProtocolConfigDTO):
        self.data = template.dict()

    def to_dto(self) -> ProtocolTemplateDTO:
        return ProtocolTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            version=self.version,
            description=self.description
        )

    def to_export_dto(self) -> ProtocolTemplateExportDTO:
        # create a new protocol to refresh the template info ()
        return ProtocolTemplateExportDTO(
            id=self.id,
            name=self.name,
            version=self.version,
            data=self.get_protocol_config_dto(),
            description=self.description
        )

    def get_protocol_config_dto(self) -> ProtocolConfigDTO:
        protocol_model = ProcessFactory.create_protocol_model_from_graph(self.get_template())
        return protocol_model.to_protocol_config_dto()

    @classmethod
    def from_protocol_model(
            cls, protocol_model: ProtocolModel, name: str, description: dict = None) -> 'ProtocolTemplate':
        protocol_template = ProtocolTemplate()
        # retrieve the protocol config, without the source task config
        protocol_template.set_template(protocol_model.to_protocol_config_dto(ignore_source_config=True))
        protocol_template.name = name
        protocol_template.description = description
        return protocol_template

    @classmethod
    def from_export_dto_dict(cls, export_dict: dict) -> 'ProtocolTemplate':
        protocol_template_dto: ProtocolTemplateExportDTO
        try:
            protocol_template_dto = ProtocolTemplateExportDTO.from_json(export_dict)
        except Exception as e:
            Logger.error(f"Error while reading the protocol template file: {e}")
            raise BadRequestException(f"The protocol template file is not valid : {e}")
        return cls.from_export_dto(protocol_template_dto)

    @classmethod
    def from_export_dto_str_bytes(cls, export_dict: StrBytes) -> 'ProtocolTemplate':
        protocol_template_dto: ProtocolTemplateExportDTO
        try:
            protocol_template_dto = ProtocolTemplateExportDTO.parse_raw(export_dict)
        except Exception as e:
            Logger.error(f"Error while reading the protocol template file: {e}")
            raise BadRequestException(f"The protocol template file is not valid : {e}")
        return cls.from_export_dto(protocol_template_dto)

    @classmethod
    def from_export_dto(cls, export_dto: ProtocolTemplateExportDTO) -> 'ProtocolTemplate':
        protocol_template = ProtocolTemplate()
        protocol_template.name = export_dto.name
        protocol_template.description = export_dto.description
        protocol_template.version = export_dto.version
        protocol_template.set_template(export_dto.data)

        return protocol_template

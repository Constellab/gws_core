

from json import loads
from typing import Dict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.protocol_template.protocol_template_dto import \
    ProtocolTemplateExportDTO


class ProtocolTemplateFactory:

    @classmethod
    def from_protocol_model(
            cls, protocol_model: ProtocolModel, name: str, description: dict = None) -> ProtocolTemplate:
        protocol_template = ProtocolTemplate()
        # retrieve the protocol config, without the source task config
        protocol_template.set_template(protocol_model.to_protocol_config_dto(ignore_source_config=True))
        protocol_template.name = name
        protocol_template.description = description
        protocol_template.version = ProtocolTemplate.CURRENT_VERSION
        return protocol_template

    @classmethod
    def from_export_dto_dict(cls, export_dict: dict) -> ProtocolTemplate:

        template_dict = cls.migrate_to_current_version(export_dict)
        protocol_template_dto: ProtocolTemplateExportDTO
        try:
            protocol_template_dto = ProtocolTemplateExportDTO.from_json(template_dict)
        except Exception as e:
            Logger.error(f"Error while reading the protocol template file: {e}")
            raise BadRequestException(f"The protocol template file is not valid : {e}")
        return cls.from_export_dto(protocol_template_dto)

    @classmethod
    def from_export_dto_str(cls, export_str: str) -> ProtocolTemplate:
        dict_: Dict
        try:
            dict_ = loads(export_str)

        except Exception as e:
            Logger.error(f"The protocol template file is not valid a valid json: {e}")
            raise BadRequestException(f"The protocol template file is not valid a valid json: {e}")

        return cls.from_export_dto_dict(dict_)

    @classmethod
    def from_export_dto(cls, export_dto: ProtocolTemplateExportDTO) -> 'ProtocolTemplate':
        protocol_template = ProtocolTemplate()
        protocol_template.name = export_dto.name
        protocol_template.description = export_dto.description
        protocol_template.version = export_dto.version
        protocol_template.set_template(export_dto.data)

        return protocol_template

    @classmethod
    def migrate_to_current_version(cls, protocol_template: dict) -> dict:
        """Migrate the protocol template to the current version

        :param protocol_template: protocol template to migrate
        :type protocol_template: ProtocolTemplate
        :return: migrated protocol template
        :rtype: ProtocolTemplate
        """
        version = protocol_template.get('version')
        if version is None:
            raise BadRequestException("The protocol template does not have a version number")

        if version == ProtocolTemplate.CURRENT_VERSION:
            return protocol_template

        if version > ProtocolTemplate.CURRENT_VERSION:
            raise BadRequestException(
                f"Protocol template version is higher than the current version: {version}. Please update your lab to support this version.")

        if version == 1:
            protocol_template["data"] = cls.migrate_data_from_1_to_3(protocol_template.get('data'))

        protocol_template['version'] = ProtocolTemplate.CURRENT_VERSION
        return protocol_template

    @classmethod
    def migrate_data_from_1_to_3(cls, graph: dict) -> dict:
        """Migrate the protocol template from version 1 to version 3

        :param protocol_template: protocol template to migrate
        :type protocol_template: ProtocolTemplate
        :return: migrated protocol template
        :rtype: ProtocolTemplate
        """
        for node in graph["nodes"].values():

            if node.get('brick_version'):
                node['brick_version_on_create'] = node.get('brick_version')
                del node['brick_version']
            node['brick_version_on_run'] = None

            if not node.get('style'):
                node['style'] = TypingStyle.default_task().to_json_dict()

            if node.get('graph'):
                cls.migrate_data_from_1_to_3(node["graph"])

            if node.get('process_typing_name') == 'TASK.gws_core.Source':
                node['config']['values']['resource_id'] = None

        return graph

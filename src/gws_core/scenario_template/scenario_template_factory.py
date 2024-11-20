

from json import loads
from typing import Dict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.scenario_template.scenario_template_dto import \
    ScenarioTemplateExportDTO


class ScenarioTemplateFactory:

    @classmethod
    def from_protocol_model(
            cls, protocol_model: ProtocolModel, name: str, description: RichTextDTO = None) -> ScenarioTemplate:
        scenario_template = ScenarioTemplate()
        # retrieve the protocol config, without the source task config
        scenario_template.set_template(protocol_model.to_protocol_config_dto(ignore_source_config=True))
        scenario_template.name = name
        scenario_template.description = description
        scenario_template.version = ScenarioTemplate.CURRENT_VERSION
        return scenario_template

    @classmethod
    def from_export_dto_dict(cls, export_dict: dict) -> ScenarioTemplate:

        template_dict = cls.migrate_to_current_version(export_dict)
        scenario_template_dto: ScenarioTemplateExportDTO
        try:
            scenario_template_dto = ScenarioTemplateExportDTO.from_json(template_dict)
        except Exception as e:
            Logger.error(f"Error while reading the scenario template file: {e}")
            raise BadRequestException(f"The scenario template file is not valid : {e}")
        return cls.from_export_dto(scenario_template_dto)

    @classmethod
    def from_export_dto_str(cls, export_str: str) -> ScenarioTemplate:
        dict_: Dict
        try:
            dict_ = loads(export_str)

        except Exception as e:
            Logger.error(f"The scenario template file is not valid a valid json: {e}")
            raise BadRequestException(f"The scenario template file is not valid a valid json: {e}")

        return cls.from_export_dto_dict(dict_)

    @classmethod
    def from_export_dto(cls, export_dto: ScenarioTemplateExportDTO) -> 'ScenarioTemplate':
        scenario_template = ScenarioTemplate()
        scenario_template.name = export_dto.name
        scenario_template.description = export_dto.description
        scenario_template.version = export_dto.version
        scenario_template.set_template(export_dto.data)

        return scenario_template

    @classmethod
    def migrate_to_current_version(cls, scenario_template: dict) -> dict:
        """Migrate the scenario template to the current version

        :param scenario_template: scenario template to migrate
        :type scenario_template: ScenarioTemplate
        :return: migrated scenario template
        :rtype: ScenarioTemplate
        """
        version = scenario_template.get('version')
        if version is None:
            raise BadRequestException("The scenario template does not have a version number")

        if version == ScenarioTemplate.CURRENT_VERSION:
            return scenario_template

        if version > ScenarioTemplate.CURRENT_VERSION:
            raise BadRequestException(
                f"Scenario template version is higher than the current version: {version}. Please update your lab to support this version.")

        if version == 1:
            scenario_template["data"] = cls.migrate_data_from_1_to_3(scenario_template.get('data'))

        scenario_template['version'] = ScenarioTemplate.CURRENT_VERSION
        return scenario_template

    @classmethod
    def migrate_data_from_1_to_3(cls, graph: dict) -> dict:
        """Migrate the scenario template from version 1 to version 3

        :param scenario_template: scenario template to migrate
        :type scenario_template: ScenarioTemplate
        :return: migrated scenario template
        :rtype: ScenarioTemplate
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

            if node.get('process_typing_name') == 'TASK.gws_core.InputTask':
                node['config']['values']['resource_id'] = None

        return graph

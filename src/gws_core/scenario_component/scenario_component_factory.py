

from json import loads
from typing import Dict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario_component.scenario_component import ScenarioComponent
from gws_core.scenario_component.scenario_component_dto import \
    ScenarioComponentExportDTO


class ScenarioComponentFactory:

    @classmethod
    def from_protocol_model(
            cls, protocol_model: ProtocolModel, name: str, description: dict = None) -> ScenarioComponent:
        scenario_component = ScenarioComponent()
        # retrieve the protocol config, without the source task config
        scenario_component.set_graph(protocol_model.to_protocol_config_dto(ignore_source_config=True))
        scenario_component.name = name
        scenario_component.description = description
        scenario_component.version = ScenarioComponent.CURRENT_VERSION
        return scenario_component

    @classmethod
    def from_export_dto_dict(cls, export_dict: dict) -> ScenarioComponent:

        template_dict = cls.migrate_to_current_version(export_dict)
        scenario_component_dto: ScenarioComponentExportDTO
        try:
            scenario_component_dto = ScenarioComponentExportDTO.from_json(template_dict)
        except Exception as e:
            Logger.error(f"Error while reading the component file: {e}")
            raise BadRequestException(f"The component file is not valid : {e}")
        return cls.from_export_dto(scenario_component_dto)

    @classmethod
    def from_export_dto_str(cls, export_str: str) -> ScenarioComponent:
        dict_: Dict
        try:
            dict_ = loads(export_str)

        except Exception as e:
            Logger.error(f"The component file is not valid a valid json: {e}")
            raise BadRequestException(f"The component file is not valid a valid json: {e}")

        return cls.from_export_dto_dict(dict_)

    @classmethod
    def from_export_dto(cls, export_dto: ScenarioComponentExportDTO) -> 'ScenarioComponent':
        scenario_component = ScenarioComponent()
        scenario_component.name = export_dto.name
        scenario_component.description = export_dto.description
        scenario_component.version = export_dto.version
        scenario_component.set_graph(export_dto.data)

        return scenario_component

    @classmethod
    def migrate_to_current_version(cls, scenario_component: dict) -> dict:
        """Migrate the component to the current version

        :param scenario_component: component to migrate
        :type scenario_component: ScenarioComponent
        :return: migrated component
        :rtype: ScenarioComponent
        """
        version = scenario_component.get('version')
        if version is None:
            raise BadRequestException("The component does not have a version number")

        if version == ScenarioComponent.CURRENT_VERSION:
            return scenario_component

        if version > ScenarioComponent.CURRENT_VERSION:
            raise BadRequestException(
                f"Scenario component version is higher than the current version: {version}. Please update your lab to support this version.")

        if version == 1:
            scenario_component["data"] = cls.migrate_data_from_1_to_3(scenario_component.get('data'))

        scenario_component['version'] = ScenarioComponent.CURRENT_VERSION
        return scenario_component

    @classmethod
    def migrate_data_from_1_to_3(cls, graph: dict) -> dict:
        """Migrate the component from version 1 to version 3

        :param scenario_component: component to migrate
        :type scenario_component: ScenarioComponent
        :return: migrated component
        :rtype: ScenarioComponent
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

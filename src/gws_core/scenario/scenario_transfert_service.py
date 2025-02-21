
from typing import Dict

from gws_core.config.config_types import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader import ScenarioDownloader
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.scenario.task.select_scenario import SelectScenario
from gws_core.scenario.task.send_scenario_to_lab import SendScenarioToLab
from gws_core.task.plug.output_task import OutputTask


class ScenarioTransfertService():

    ################################### CREATE SCENARIO FROM LINK ##############################

    @classmethod
    def import_from_lab(cls, values: ConfigParamsDict) -> Scenario:
        # Create a scenario containing 1 scenario downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(title="Import scenario")
        protocol = scenario.get_protocol()

        # Add the importer and the connector
        downloader = protocol.add_process(ScenarioDownloader, 'downloader', values)

        # Add output and connect it
        output_task = protocol.add_output('output', downloader >> ScenarioDownloader.OUTPUT_NAME, False)

        scenario.run()

        # return the resource model of the output process
        output_task.refresh()
        scenario_resource: ScenarioResource = output_task.get_input(OutputTask.input_name)

        return scenario_resource.get_scenario()

    @classmethod
    def get_import_scenario_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return ScenarioDownloader.get_config_specs_dto()

    @classmethod
    def export_scenario_to_lab(cls, scenario_id: str, values: ConfigParamsDict) -> None:

        # Create a scenario containing 1 scenario downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(title="Send scenario")
        protocol = scenario.get_protocol()

        # Select the scenario > Send it to the lab
        select_scenario = protocol.add_process(SelectScenario, 'selector', {SelectScenario.CONFIG_NAME: scenario_id})
        send = protocol.add_process(SendScenarioToLab, 'sender', values)

        # Connect the processes
        protocol.add_connector(
            select_scenario.get_output_port(SelectScenario.OUTPUT_NAME),
            send.get_input_port(SendScenarioToLab.INPUT_NAME))

        scenario.run()

    @classmethod
    def get_export_scenario_to_lab_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return SendScenarioToLab.get_config_specs_dto()

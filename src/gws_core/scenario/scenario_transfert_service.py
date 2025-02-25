
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

    @classmethod
    def import_from_lab_sync(cls, values: ConfigParamsDict) -> Scenario:
        """ Run the import scenario synchronously and wait for it to finished and return the imported scenario
        """
        scenario: ScenarioProxy = cls._build_import_from_lab(values)

        scenario.run()

        # return the resource model of the output process
        output_task = scenario.get_protocol().get_process('output').refresh()
        scenario_resource: ScenarioResource = output_task.get_input(OutputTask.input_name)

        return scenario_resource.get_scenario()

    @classmethod
    def import_from_lab_async(cls, values: ConfigParamsDict) -> Scenario:
        """ Run the import scenario asynchronously, return the running import scenario
        """

        scenario: ScenarioProxy = cls._build_import_from_lab(values)

        scenario.run_async()
        return scenario.get_model().refresh()

    @classmethod
    def _build_import_from_lab(cls, values: ConfigParamsDict) -> ScenarioProxy:
        # Create a scenario containing 1 scenario downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(title="Import scenario")
        protocol = scenario.get_protocol()

        # Add the importer and the connector
        downloader = protocol.add_process(ScenarioDownloader, 'downloader', values)

        # Add output and connect it
        protocol.add_output('output', downloader >> ScenarioDownloader.OUTPUT_NAME, False)

        return scenario

    @classmethod
    def get_import_scenario_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return ScenarioDownloader.get_config_specs_dto()

    @classmethod
    def export_scenario_to_lab(cls, scenario_id: str, values: ConfigParamsDict) -> Scenario:
        """ Export a scenario to a lab synchronously and return the newly created scenario that
        exportes the scenario to the lab
        """
        scenario = cls._build_export_scenario_to_lab(scenario_id, values)

        scenario.run()

        return scenario.get_model().refresh()

    @classmethod
    def export_scenario_to_lab_async(cls, scenario_id: str, values: ConfigParamsDict) -> Scenario:
        """ Export a scenario to a lab asynchronously and return the newly created scenario that
        exports the scenario to the lab
        """
        scenario = cls._build_export_scenario_to_lab(scenario_id, values)

        scenario.run_async()

        return scenario.get_model().refresh()

    @classmethod
    def _build_export_scenario_to_lab(cls, scenario_id: str, values: ConfigParamsDict) -> ScenarioProxy:

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

        return scenario

    @classmethod
    def get_export_scenario_to_lab_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return SendScenarioToLab.get_config_specs_dto()

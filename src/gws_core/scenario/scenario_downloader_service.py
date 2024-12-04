
from typing import Dict

from gws_core.config.config_types import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader import ScenarioDownloader
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.plug.output_task import OutputTask


class ScenarioDownloaderService():

    ################################### CREATE SCENARIO FROM LINK ##############################

    @classmethod
    def import_from_lab(cls, values: ConfigParamsDict) -> Scenario:
        """Create an scenario from a link

        This is not in the ScenarioService to avoid circular imports
        :param user: the user that create the scenario
        :type user: User
        :param link: the link to create the scenario
        :type link: str
        :return: the created scenario
        :rtype: Scenario
        """

        # Create an scenario containing 1 scenario downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(None, title="Import scenario")
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

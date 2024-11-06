
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader import (ScenarioDownloader,
                                                        ScenarioDownloaderMode)
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.plug import OutputTask


class ScenarioDownloaderService():

    ################################### CREATE SCENARIO FROM LINK ##############################

    @classmethod
    def import_from_lab(cls, link: str, mode: ScenarioDownloaderMode) -> Scenario:
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
        downloader = protocol.add_process(ScenarioDownloader, 'downloader',
                                          ScenarioDownloader.build_config(link=link, mode=mode))

        # Add output and connect it
        output_task = protocol.add_output('output', downloader >> ScenarioDownloader.OUTPUT_NAME, False)

        scenario.run()

        # return the resource model of the output process
        output_task.refresh()
        scenario_resource: ScenarioResource = output_task.get_input(OutputTask.input_name)

        return scenario_resource.get_scenario()

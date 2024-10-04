
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader import (ScenarioDownloader,
                                                        ScenarioDownloaderMode)
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.plug import Sink


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

        # Create an scenario containing 1 scenario downloader , 1 sink
        scenario: ScenarioProxy = ScenarioProxy(None, title="Import scenario")
        protocol = scenario.get_protocol()

        # Add the importer and the connector
        downloader = protocol.add_process(ScenarioDownloader, 'downloader',
                                          ScenarioDownloader.build_config(link=link, mode=mode))

        # Add sink and connect it
        sink = protocol.add_sink('sink', downloader >> ScenarioDownloader.OUTPUT_NAME, False)

        scenario.run()

        # return the resource model of the sink process
        sink.refresh()
        scenario_resource: ScenarioResource = sink.get_input(Sink.input_name)

        return scenario_resource.get_scenario()

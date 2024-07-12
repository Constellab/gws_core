
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.task.experiment_downloader import (
    ExperimentDownloader, ExperimentDownloaderMode)
from gws_core.experiment.task.experiment_resource import ExperimentResource
from gws_core.task.plug import Sink


class ExperimentDownloaderService():

    ################################### CREATE EXPERIMENT FROM LINK ##############################

    @classmethod
    def import_from_lab(cls, link: str, mode: ExperimentDownloaderMode) -> Experiment:
        """Create an experiment from a link

        This is not in the ExperimentService to avoid circular imports
        :param user: the user that create the experiment
        :type user: User
        :param link: the link to create the experiment
        :type link: str
        :return: the created experiment
        :rtype: Experiment
        """

        # Create an experiment containing 1 experiment downloader , 1 sink
        experiment: IExperiment = IExperiment(None, title="Import experiment")
        protocol = experiment.get_protocol()

        # Add the importer and the connector
        downloader = protocol.add_process(ExperimentDownloader, 'downloader',
                                          ExperimentDownloader.build_config(link=link, mode=mode))

        # Add sink and connect it
        sink = protocol.add_sink('sink', downloader >> ExperimentDownloader.OUTPUT_NAME, False)

        experiment.run()

        # return the resource model of the sink process
        sink.refresh()
        experiment_resource: ExperimentResource = sink.get_input(Sink.input_name)

        return experiment_resource.get_experiment()

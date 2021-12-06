# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from inspect import isclass
from typing import Type

from ..experiment.experiment_dto import ExperimentDTO
from ..experiment.experiment_run_service import ExperimentRunService
from ..protocol.protocol import Protocol
from ..protocol.protocol_interface import IProtocol
from ..study.study import Study
from ..study.study_dto import StudyDto
from .experiment import Experiment, ExperimentType
from .experiment_service import ExperimentService


class IExperiment:
    """Object to simplify experiment creation, configuration and run.
    This can be used in a Jupyter Notebook

    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _experiment: Experiment
    _protocol: IProtocol

    def __init__(
            self, protocol_type: Type[Protocol] = None, study: Study = None, title: str = '', description: str = '',
            type_: ExperimentType = ExperimentType.EXPERIMENT):
        """This create an experiment in the database with the provided Task or Protocol

        :param process_type: Can be the type of a Protocol or a Task.
                            If this is a task, it will be wrapped in a protocol
                            If none it will create an empty protocol in the experiment
        :type process_type: Type[Process]
        :param study: experiment title, defaults to ''
        :type study: str, optional
        :param title: experiment title, defaults to ''
        :type title: str, optional
        :param description: experiment description, defaults to ''
        :type description: str, optional
        :param type_: type fo the experiment, to change only if you want what you are doing, defaults to ExperimentType.EXPERIMENT
        :type type_: str, optional
        :raises Exception: [description]
        """

        if protocol_type is None:
            self._experiment = ExperimentService.create_empty_experiment(
                title=title, description=description, study=study, type_=type_)
        else:
            if not isclass(protocol_type) or not issubclass(protocol_type, Protocol):
                raise Exception(f"The provided process_type '{str(protocol_type)}' is not a process")
            self._experiment = ExperimentService.create_experiment_from_protocol_type(
                protocol_type=protocol_type, title=title, description=description, study=study, type_=type_)

        # Init the IProtocol
        self._protocol = IProtocol(self._experiment.protocol_model)

    def get_protocol(self) -> IProtocol:
        """retrieve the main protocol of the experiment
        """
        return self._protocol

    async def run(self) -> None:
        """exceute the experiment, after that the resource should be generated and can be retrieve by process
        """
        await ExperimentRunService.run_experiment(experiment=self._experiment)

    def reset(self) -> None:
        """Reset the status and the resources of the experiment, its protocols and tasks
        """
        self._experiment.reset()

    def stop(self) -> None:
        ExperimentRunService.stop_experiment(self._experiment.id)

    def get_experiment_model(self) -> Experiment:
        return self._experiment

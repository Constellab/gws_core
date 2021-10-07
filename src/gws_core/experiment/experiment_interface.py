# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from inspect import isclass
from typing import Type

from gws_core.study.study_dto import StudyDto

from ..experiment.experiment_dto import ExperimentDTO
from ..process.process import Process
from ..protocol.protocol import Protocol
from ..protocol.protocol_interface import IProtocol
from ..study.study import Study
from ..task.task import Task
from .experiment import Experiment
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
            self, protocol_type: Type[Protocol] = None, study: Study = None, title: str = '', description: str = ''):
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
        :raises Exception: [description]
        """

        if protocol_type is None:
            study_dto: StudyDto = None
            if study is not None:
                study_dto = StudyDto(uri=study.uri, title=study.title, description=study.description)
            self._experiment = ExperimentService.create_empty_experiment(
                ExperimentDTO(title=title, description=description, study=study_dto))

        else:
            if not isclass(protocol_type) or not issubclass(protocol_type, Protocol):
                raise Exception(f"The provided process_type '{str(protocol_type)}' is not a process")
            self._experiment = ExperimentService.create_experiment_from_protocol_type(
                protocol_type=protocol_type, title=title, description=description, study=study)

        # Init the IProtocol
        self._protocol = IProtocol(self._experiment.protocol_model)

    def get_protocol(self) -> IProtocol:
        """retrieve the main protocol of the experiment
        """
        return self._protocol

    async def run(self) -> None:
        """exceute the experiment, after that the resource should be generated and can be retrieve by process
        """
        await ExperimentService.run_experiment(experiment=self._experiment)

    def reset(self) -> None:
        """Reset the status and the resources of the experiment, its protocols and tasks
        """
        self._experiment.reset()

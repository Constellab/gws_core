# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from inspect import isclass
from typing import Type

from ..study.study import Study

from ..experiment.experiment_dto import ExperimentDTO
from ..process.process import Process
from ..protocol.protocol import Protocol
from ..protocol.protocol_interface import IProtocol
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

    _process_type: Type[Process]
    _experiment: Experiment
    _protocol: IProtocol

    def __init__(self, process_type: Type[Process] = None, study: Study = None, title: str = '', description: str = ''):
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
        self._process_type = process_type

        if process_type is None:
            self._experiment = ExperimentService.create_empty_experiment(
                ExperimentDTO(title=title, description=description))

        else:
            if not isclass(process_type) or not issubclass(process_type, Process):
                raise Exception(f"The provided process_type '{str(process_type)}' is not a process")

            if issubclass(process_type, Task):
                self._experiment = ExperimentService.create_experiment_from_task_type(
                    task_type=process_type, title=title, description=description)
            elif issubclass(process_type, Protocol):
                self._experiment = ExperimentService.create_experiment_from_protocol_type(
                    protocol_type=process_type, title=title, description=description)

        # Init the IProtocol
        self._protocol = IProtocol(self._experiment.protocol_model, None)

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

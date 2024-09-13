

from inspect import isclass
from multiprocessing import Process
from time import sleep
from typing import List, Type

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.tag import Tag
from gws_core.tag.tag_service import TagService

from ..experiment.experiment_run_service import ExperimentRunService
from ..folder.space_folder import SpaceFolder
from ..protocol.protocol import Protocol
from ..protocol.protocol_interface import IProtocol
from .experiment import Experiment
from .experiment_enums import ExperimentCreationType
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
            self, protocol_type: Type[Protocol] = None, folder: SpaceFolder = None, title: str = '',
            creation_type: ExperimentCreationType = ExperimentCreationType.AUTO):
        """This create an experiment in the database with the provided Task or Protocol

        :param process_type: Can be the type of a Protocol or a Task.
                            If this is a task, it will be wrapped in a protocol
                            If none it will create an empty protocol in the experiment
        :type process_type: Type[Process]
        :param folder: experiment title, defaults to ''
        :type folder: str, optional
        :param title: experiment title, defaults to ''
        :type title: str, optional
        :param creation_type: type of the created experiment, defaults to ExperimentExecutionType.AUTO
        :type creation_type: ExperimentExecutionType, optional
        :raises Exception: [description]
        """

        if protocol_type is None:
            self._experiment = ExperimentService.create_experiment(
                title=title, folder_id=folder, creation_type=creation_type)
        else:
            if not isclass(protocol_type) or not issubclass(protocol_type, Protocol):
                raise Exception(
                    f"The provided process_type '{str(protocol_type)}' is not a process")
            self._experiment = ExperimentService.create_experiment_from_protocol_type(
                protocol_type=protocol_type, title=title, folder=folder, creation_type=creation_type)

        # Init the IProtocol
        self._protocol = IProtocol(self._experiment.protocol_model)

    def get_protocol(self) -> IProtocol:
        """retrieve the main protocol of the experiment
        """
        return self._protocol

    def run(self, auto_delete_if_error: bool = False) -> None:
        """execute the experiment, after that the resource should be generated and can be retrieve by process
        """

        # run the experiment in a sub process so it can be stopped
        process = Process(
            target=ExperimentRunService.run_experiment, args=(self._experiment,))
        process.start()
        process.join()

        self.refresh()

        if self._experiment.is_error:
            if auto_delete_if_error:
                self.delete()
            raise Exception(self._experiment.get_error_info().detail)

        # when stop manually the experiment, wait a bit for the status to be updated
        # because the experiment status is updated after the process is stopped
        if process.exitcode is None:
            sleep(2)
            self.refresh()
            if self._experiment.is_error:
                raise Exception(self._experiment.get_error_info().detail)

        if process.exitcode != 0:
            raise Exception("Error in during the execution of the experiment")

    def stop(self) -> None:
        ExperimentRunService.stop_experiment(self._experiment.id)

    def delete(self) -> None:
        ExperimentService.delete_experiment(self._experiment.id)

    def get_model(self) -> Experiment:
        return self._experiment

    def get_model_id(self) -> str:
        return self._experiment.id

    def is_running(self) -> bool:
        return self._experiment.is_running

    def is_finished(self) -> bool:
        return self._experiment.is_finished

    def is_success(self) -> bool:
        return self._experiment.is_success

    def add_tag(self, tag: Tag) -> None:
        TagService.add_tag_to_entity(EntityType.EXPERIMENT, self._experiment.id,
                                     tag)

    def add_tags(self, tags: List[Tag]) -> None:
        TagService.add_tags_to_entity(EntityType.EXPERIMENT, self._experiment.id,
                                      tags)

    def refresh(self) -> 'IExperiment':
        self._experiment = self._experiment.refresh()
        self._protocol.refresh()

        return self

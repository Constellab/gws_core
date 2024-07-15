

from typing import Optional

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_enums import ExperimentCreationType
from gws_core.experiment.experiment_zipper import (ZipExperiment,
                                                   ZipExperimentInfo)
from gws_core.project.project import Project
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO
from gws_core.protocol.protocol_graph_factory import ProtocolGraphFactory
from gws_core.protocol.protocol_model import ProtocolModel


class ExperimentLoader():

    exp_info: ZipExperimentInfo

    _experiment: Experiment
    _protocol_model: ProtocolModel

    _message_dispatcher: MessageDispatcher

    def __init__(self, experiment_info: ZipExperimentInfo,
                 message_dispatcher: Optional[MessageDispatcher] = None) -> None:
        self.exp_info = experiment_info

        if message_dispatcher is None:
            self._message_dispatcher = MessageDispatcher()
        else:
            self._message_dispatcher = message_dispatcher

    def load_experiment(self) -> Experiment:

        self._experiment = self._load_experiment(self.exp_info.experiment)

        # load the protocol
        protocol_model = self._load_protocol_model(self.exp_info.protocol)
        protocol_model.set_experiment(self._experiment)
        self._protocol_model = protocol_model

        return self._experiment

    def _load_experiment(self, zip_experiment: ZipExperiment) -> Experiment:
        # create the experiment and load the info
        experiment = Experiment()
        experiment.title = zip_experiment.title
        experiment.creation_type = ExperimentCreationType.IMPORTED
        experiment.description = zip_experiment.description
        experiment.status = zip_experiment.status

        if zip_experiment.project is not None:
            project = Project.get_by_id(zip_experiment.project.id)

            if project is None:
                self._message_dispatcher.notify_info_message(
                    f"Project '{zip_experiment.project.code}' not found, skipping linking experiment to project.")
            else:
                experiment.project = project

        if zip_experiment.error_info is not None:
            experiment.set_error_info(zip_experiment.error_info)

        return experiment

    def _load_protocol_model(self, protocol: ExperimentProtocolDTO) -> ProtocolModel:
        return ProtocolGraphFactory.create_protocol_model_from_config(protocol.data)

    def get_experiment(self) -> Experiment:
        if self._experiment is None:
            raise Exception("Experiment not loaded, call load_experiment first")
        return self._experiment

    def get_protocol_model(self) -> ProtocolModel:
        if self._protocol_model is None:
            raise Exception("Protocol model not loaded, call load_experiment first")

        return self._protocol_model

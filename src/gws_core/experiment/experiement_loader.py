

import os
from json import load

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_zipper import (ExperimentZipper,
                                                   ZipExperiment,
                                                   ZipExperimentInfo)
from gws_core.impl.file.file_helper import FileHelper
from gws_core.process.process_factory import ProcessFactory
from gws_core.project.project import Project
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO
from gws_core.protocol.protocol_model import ProtocolModel


class ExperimentLoader():

    info_json: ZipExperimentInfo

    experiment_folder: str

    experiment: Experiment
    protocol_model: ProtocolModel

    _message_dispatcher: MessageDispatcher

    def __init__(self, experiment_folder: str, message_dispatcher: MessageDispatcher = None) -> None:
        self.info_json = None
        self.experiment_folder = experiment_folder

        if message_dispatcher is None:
            self._message_dispatcher = MessageDispatcher()
        else:
            self._message_dispatcher = message_dispatcher

    def load_experiment(self) -> Experiment:

        zip_experiment = self._load_info_json()

        self.experiment = self._load_experiment(zip_experiment.experiment)

        # load the protocol
        protocol_model = self._load_protocol_model(zip_experiment.protocol)
        protocol_model.set_experiment(self.experiment)
        self.protocol_model = protocol_model

        return self.experiment

    def _load_experiment(self, zip_experiment: ZipExperiment) -> Experiment:
        # create the experiment and load the info
        experiment = Experiment()
        experiment.title = zip_experiment.title
        # TODO : check if the description is a valid rich text
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
        return ProcessFactory.create_protocol_model_from_graph(protocol.data.graph)

    def _load_info_json(self) -> ZipExperimentInfo:
        if self.info_json is not None:
            return self.info_json

        info_json_path = os.path.join(
            self.experiment_folder, ExperimentZipper.INFO_JSON_FILE_NAME)

        if not FileHelper.exists_on_os(info_json_path):
            raise Exception(
                f'File {info_json_path} not found in the zip file.')

        info_json: dict = None
        with open(info_json_path, 'r', encoding='UTF-8') as file:
            info_json = load(file)

        if info_json is None:
            raise Exception(f'File {info_json_path} is empty.')

        if not isinstance(info_json.get('zip_version'), int):
            raise Exception(
                f"The zip_version value '{info_json.get('zip_version')}' in {info_json_path} file is invalid, must be an int")

        self.info_json = ZipExperimentInfo.from_json(info_json)

        return self.info_json

    def delete_experiment_folder(self):
        """Delete the experiment folder
        """
        FileHelper.delete_dir(self.experiment_folder)

    @classmethod
    def from_compress_file(cls, compress_file_path: str) -> 'ExperimentLoader':
        """Uncompress a file and create a ResourceLoader
        """
        temp_dir = Settings.get_instance().make_temp_dir()
        Compress.smart_decompress(compress_file_path, temp_dir)
        return ExperimentLoader(temp_dir)

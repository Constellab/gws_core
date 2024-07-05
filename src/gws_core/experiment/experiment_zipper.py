

import os
from json import dump
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.project.project_dto import ProjectDTO
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO
from gws_core.user.user import User


class ZipExperiment(BaseModelDTO):
    id: str
    title: str
    description: Optional[dict]
    status: ExperimentStatus
    project: Optional[ProjectDTO]
    error_info: Optional[ProcessErrorInfo]


class ZipExperimentInfo(BaseModelDTO):
    """ Content of the info.json file in the zip file when a resource is zipped"""
    zip_version: int
    experiment: ZipExperiment
    protocol: ExperimentProtocolDTO
    # resources: List[ZipExperiment]
    origin: ExternalLabWithUserInfo


class ExperimentZipper():
    """ Class to generate
    a zip file containing everything needed to recreate an experiment"""

    ZIP_FILE_NAME = 'experiment.zip'
    RESOURCE_FOLDER_NAME = 'resources'
    INFO_JSON_FILE_NAME = 'info.json'
    COMPRESS_EXTENSION = 'zip'

    temp_dir: str

    zip: ZipCompress

    experimeny_zip: ZipExperiment
    protocol: ExperimentProtocolDTO
    shared_by: User

    def __init__(self, shared_by: User):
        self.shared_by = shared_by
        self.temp_dir = Settings.get_instance().make_temp_dir()
        self.zip = ZipCompress(self.get_zip_file_path())

    def add_experiment(self, experiment_id: str) -> None:
        experiment = Experiment.get_by_id_and_check(experiment_id)

        self.experimeny_zip = ZipExperiment(
            id=experiment.id,
            title=experiment.title,
            description=experiment.description,
            status=experiment.status,
            project=experiment.project.to_dto() if experiment.project is not None else None,
            error_info=experiment.error_info
        )

        self.protocol = experiment.export_protocol()

    def close_zip(self) -> str:

        experiment_zip_info = ZipExperimentInfo(
            zip_version=1,
            experiment=self.experimeny_zip,
            protocol=self.protocol,
            origin=ExternalLabService.get_current_lab_info(self.shared_by)
        )
        # add the info.json file
        info_json = os.path.join(self.temp_dir, self.INFO_JSON_FILE_NAME)
        with open(info_json, 'w', encoding='UTF-8') as file:
            dump(experiment_zip_info.to_json_dict(), file)

        self.zip.add_file(info_json, file_name=self.INFO_JSON_FILE_NAME)
        self.zip.close()

        return self.get_zip_file_path()

    def get_zip_file_path(self):
        return os.path.join(self.temp_dir, self.ZIP_FILE_NAME)

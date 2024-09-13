
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO


class ZipExperiment(BaseModelDTO):
    id: str
    title: str
    description: Optional[dict]
    status: ExperimentStatus
    folder: Optional[SpaceFolderDTO]
    error_info: Optional[ProcessErrorInfo]


class ZipExperimentInfo(BaseModelDTO):
    """ Content of the info.json file in the zip file when a resource is zipped"""
    zip_version: int
    experiment: ZipExperiment
    protocol: ExperimentProtocolDTO

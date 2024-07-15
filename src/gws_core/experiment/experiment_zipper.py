
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.project.project_dto import ProjectDTO
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO


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

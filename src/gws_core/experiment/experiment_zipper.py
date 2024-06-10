

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.service.external_lab_service import ExternalLabWithUserInfo
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.project.project_dto import ProjectDTO


class ZipExperiment(BaseModelDTO):
    id: str
    title: str
    description: Optional[dict]
    protocol: dict
    status: ExperimentStatus
    project: Optional[ProjectDTO]


class ZipExperimentResource(BaseModelDTO):
    zip_file_name: str


class ZipProcess(BaseModelDTO):
    id: str
    parent_protocol_id: str
    experiment_id: str
    instance_name: str
    config_data: dict
    progress_bar: dict
    process_typing_name: str
    brick_version_on_create: str
    brick_version_on_run: Optional[str]
    status: ProcessStatus
    error_info: ProcessErrorInfo
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    data: dict


class ZipExperimentInfo(BaseModelDTO):
    """ Content of the info.json file in the zip file when a resource is zipped"""
    zip_version: int
    experiment: ZipExperiment
    resources: List[ZipExperiment]
    origin: ExternalLabWithUserInfo

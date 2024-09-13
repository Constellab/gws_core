

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.experiment.experiment_enums import (ExperimentCreationType,
                                                  ExperimentProcessStatus,
                                                  ExperimentStatus)
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.progress_bar.progress_bar_dto import ProgressBarMessageDTO
from gws_core.user.user_dto import UserDTO


# DTO to create/update an experiment
class ExperimentSaveDTO(BaseModelDTO):
    folder_id: Optional[str] = None
    title: str = None
    protocol_template_id: Optional[str] = None
    protocol_template_json: Optional[dict] = None


class RunningProcessInfo(BaseModelDTO):
    id: str
    title: str
    last_message: Optional[ProgressBarMessageDTO]
    progression: float


class RunningExperimentInfoDTO(BaseModelDTO):
    id: str
    title: str = None
    folder: Optional[SpaceFolderDTO]
    running_tasks: List[RunningProcessInfo]


class ExperimentDTO(ModelWithUserDTO):
    title: str
    description: Optional[dict]
    creation_type: ExperimentCreationType
    protocol: dict
    status: ExperimentStatus
    is_validated: bool
    validated_by: Optional[UserDTO]
    validated_at: Optional[datetime]
    last_sync_by: Optional[UserDTO]
    last_sync_at: Optional[datetime]
    is_archived: bool
    folder: Optional[SpaceFolderDTO]
    pid_status: ExperimentProcessStatus


class ExperimentCountByTitleResultDTO(BaseModelDTO):
    count: int


class ExperimentSimpleDTO(BaseModelDTO):
    id: str
    title: str

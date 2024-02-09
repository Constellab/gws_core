# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.entity_navigator.entity_navigator_type import EntityNavGroupDTO
from gws_core.experiment.experiment_enums import (ExperimentProcessStatus,
                                                  ExperimentStatus,
                                                  ExperimentType)
from gws_core.progress_bar.progress_bar_dto import ProgressBarMessageDTO
from gws_core.project.project_dto import ProjectDTO
from gws_core.user.user_dto import UserDTO


# DTO to create/update an experiment
class ExperimentSaveDTO(BaseModel):
    project_id: Optional[str] = None
    title: str = None
    protocol_template_id: Optional[str] = None
    protocol_template_json: Optional[dict] = None


class RunningProcessInfo(BaseModelDTO):
    id: str
    title: str
    last_message: ProgressBarMessageDTO
    progression: float


class RunningExperimentInfoDTO(BaseModelDTO):
    id: str
    title: str = None
    project: Optional[ProjectDTO]
    running_tasks: List[RunningProcessInfo]


class ExperimentDTO(ModelWithUserDTO):
    title: str
    description: Optional[dict]
    type: ExperimentType
    protocol: dict
    status: ExperimentStatus
    is_validated: bool
    validated_by: Optional[UserDTO]
    validated_at: Optional[datetime]
    last_sync_by: Optional[UserDTO]
    last_sync_at: Optional[datetime]
    is_archived: bool
    project: Optional[ProjectDTO]
    pid_status: ExperimentProcessStatus


class ExperimentCountByTitleResultDTO(BaseModelDTO):
    count: int


class ExperimentSimpleDTO(BaseModelDTO):
    id: str
    title: str

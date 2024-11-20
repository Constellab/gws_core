

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.progress_bar.progress_bar_dto import ProgressBarMessageDTO
from gws_core.scenario.scenario_enums import (ScenarioCreationType,
                                              ScenarioProcessStatus,
                                              ScenarioStatus)
from gws_core.user.user_dto import UserDTO


# DTO to create/update an scenario
class ScenarioSaveDTO(BaseModelDTO):
    folder_id: Optional[str] = None
    title: str = None
    scenario_template_id: Optional[str] = None
    scenario_template_json: Optional[dict] = None


class RunningProcessInfo(BaseModelDTO):
    id: str
    title: str
    last_message: Optional[ProgressBarMessageDTO]
    progression: float


class RunningScenarioInfoDTO(BaseModelDTO):
    id: str
    title: str = None
    folder: Optional[SpaceFolderDTO]
    running_tasks: List[RunningProcessInfo]


class ScenarioDTO(ModelWithUserDTO):
    title: str
    description: Optional[RichTextDTO]
    creation_type: ScenarioCreationType
    protocol: dict
    status: ScenarioStatus
    is_validated: bool
    validated_by: Optional[UserDTO]
    validated_at: Optional[datetime]
    last_sync_by: Optional[UserDTO]
    last_sync_at: Optional[datetime]
    is_archived: bool
    folder: Optional[SpaceFolderDTO]
    pid_status: ScenarioProcessStatus


class ScenarioCountByTitleResultDTO(BaseModelDTO):
    count: int


class ScenarioSimpleDTO(BaseModelDTO):
    id: str
    title: str

from datetime import datetime

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.progress_bar.progress_bar_dto import ProgressBarMessageDTO
from gws_core.scenario.scenario_enums import (
    ScenarioCreationType,
    ScenarioProcessStatus,
    ScenarioStatus,
)
from gws_core.user.user_dto import UserDTO


# DTO to create/update a scenario
class ScenarioSaveDTO(BaseModelDTO):
    folder_id: str | None = None
    title: str = None
    scenario_template_id: str | None = None
    scenario_template_json: dict | None = None


class RunningProcessInfo(BaseModelDTO):
    id: str
    title: str
    last_message: ProgressBarMessageDTO | None
    progression: float


class RunningScenarioInfoDTO(BaseModelDTO):
    id: str
    title: str = None
    folder: SpaceFolderDTO | None
    running_tasks: list[RunningProcessInfo]


class ScenarioDTO(ModelWithUserDTO):
    title: str
    description: RichTextDTO | None
    creation_type: ScenarioCreationType
    protocol: dict
    status: ScenarioStatus
    is_validated: bool
    validated_by: UserDTO | None
    validated_at: datetime | None
    last_sync_by: UserDTO | None
    last_sync_at: datetime | None
    is_archived: bool
    folder: SpaceFolderDTO | None
    pid_status: ScenarioProcessStatus


class ScenarioCountByTitleResultDTO(BaseModelDTO):
    count: int


class ScenarioSimpleDTO(BaseModelDTO):
    id: str
    title: str


class ScenarioProgressDTO(BaseModelDTO):
    progress: int = None
    last_message: ProgressBarMessageDTO | None = None

    def get_last_message_content(self) -> str | None:
        return self.last_message.text if self.last_message else None

    def has_last_message(self) -> bool:
        return self.last_message is not None

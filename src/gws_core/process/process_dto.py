from datetime import datetime

from gws_core.config.config_dto import ConfigDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.io.io_dto import IODTO
from gws_core.model.typing_dto import SimpleTypingDTO, TypingStatus
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.progress_bar.progress_bar_dto import ProgressBarDTO
from gws_core.user.user_dto import UserDTO


class ProcessDTO(ModelWithUserDTO):
    parent_protocol_id: str | None
    scenario_id: str | None
    instance_name: str
    config: ConfigDTO
    progress_bar: ProgressBarDTO
    process_typing_name: str
    brick_version_on_create: str
    brick_version_on_run: str | None
    run_by: UserDTO | None
    status: ProcessStatus
    error_info: ProcessErrorInfo | None
    started_at: datetime | None
    ended_at: datetime | None
    is_archived: bool
    is_protocol: bool
    inputs: IODTO
    outputs: IODTO
    type_status: TypingStatus
    process_type: SimpleTypingDTO | None = None
    name: str | None = None
    community_agent_version_id: str | None = None
    community_agent_version_modified: bool | None = None
    style: TypingStyle = None
    is_agent: bool = False

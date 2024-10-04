

from datetime import datetime
from typing import Optional

from gws_core.config.config_dto import ConfigDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.io.io_dto import IODTO
from gws_core.model.typing_dto import SimpleTypingDTO, TypingStatus
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.progress_bar.progress_bar_dto import ProgressBarDTO


class ProcessDTO(ModelWithUserDTO):
    parent_protocol_id: Optional[str]
    scenario_id: Optional[str]
    instance_name: str
    config: ConfigDTO
    progress_bar: ProgressBarDTO
    process_typing_name: str
    brick_version_on_create: str
    brick_version_on_run: Optional[str]
    status: ProcessStatus
    error_info: Optional[ProcessErrorInfo]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    is_archived: bool
    is_protocol: bool
    inputs: IODTO
    outputs: IODTO
    type_status: TypingStatus
    process_type: Optional[SimpleTypingDTO] = None
    name: Optional[str] = None
    community_live_task_version_id: Optional[str] = None
    style: TypingStyle = None

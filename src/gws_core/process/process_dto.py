# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import Optional

from gws_core.config.config_dto import ConfigDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.io.io_dto import IODTO
from gws_core.model.typing_dict import TypingStatus
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.progress_bar.progress_bar_dto import ProgressBarDTO


class ProcessDTO(ModelWithUserDTO):
    parent_protocol_id: Optional[str]
    experiment_id: Optional[str]
    instance_name: str
    config: ConfigDTO
    progress_bar: ProgressBarDTO
    process_typing_name: str
    brick_version: str
    status: ProcessStatus
    error_info: Optional[ProcessErrorInfo]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    is_archived: bool
    is_protocol: bool
    inputs: IODTO
    outputs: IODTO
    human_name: Optional[str] = None
    short_description: Optional[str] = None
    type_status: TypingStatus

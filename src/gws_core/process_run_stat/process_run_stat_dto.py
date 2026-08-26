from datetime import datetime
from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO

ProcessRunStatLabEnv = Literal["PROD", "DEV"]
ProcessRunStatStatus = Literal[
    "DRAFT", "RUNNING", "SUCCESS", "ERROR", "PARTIALLY_RUN", "WAITING_FOR_CLI_PROCESS"
]


class ProcessRunStatDTO(ModelDTO):
    process_typing_name: str
    community_agent_version_id: str | None
    status: ProcessRunStatStatus
    error_info: dict | None
    started_at: datetime
    ended_at: datetime
    elapsed_time: float
    brick_version_on_run: str
    brick_version_on_create: str
    config_value: dict
    lab_env: ProcessRunStatLabEnv
    executed_by: str
    sync_with_community: bool


class ProcessRunStatCreateDTO(BaseModelDTO):
    """Values needed to create a ProcessRunStatModel.

    Same fields as ProcessRunStatDTO, without the ones the model owns itself
    (id, dates and sync_with_community).
    """

    process_typing_name: str
    status: ProcessRunStatStatus
    started_at: datetime
    ended_at: datetime
    elapsed_time: float
    brick_version_on_run: str
    brick_version_on_create: str
    config_value: dict
    lab_env: ProcessRunStatLabEnv
    executed_by: str
    error_info: dict | None = None
    community_agent_version_id: str | None = None

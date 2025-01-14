from datetime import datetime
from typing import Dict, Literal, Optional

from gws_core.core.model.model_dto import ModelDTO

RunStatLabEnv = Literal['PROD', 'DEV']
RunStatStatus = Literal['DRAFT', 'RUNNING', 'SUCCESS', 'ERROR', 'PARTIALLY_RUN', 'WAITING_FOR_CLI_PROCESS']


class RunStatDTO(ModelDTO):
    process_typing_name: str
    community_agent_version_id: Optional[str]
    status: RunStatStatus
    error_info: Optional[Dict]
    started_at: datetime
    ended_at: datetime
    elapsed_time: float
    brick_version_on_run: str
    brick_version_on_create: str
    config_value: Dict
    lab_id: str
    lab_env: RunStatLabEnv
    executed_by: str
    sync_with_community: bool

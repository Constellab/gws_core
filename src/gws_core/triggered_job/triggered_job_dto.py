from datetime import datetime

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.model.typing_dto import TypingRefDTO
from gws_core.triggered_job.triggered_job_types import (
    JobRunTrigger,
    JobStatus,
    TriggerType,
)


class TriggeredJobRunDTO(ModelDTO):
    """DTO for a triggered job run"""

    triggered_job_id: str
    trigger: JobRunTrigger
    scenario_id: str | None
    started_at: datetime
    ended_at: datetime | None
    status: JobStatus
    error_info: dict | None
    duration_seconds: float | None = None


class TriggeredJobDTO(ModelWithUserDTO):
    """DTO for a triggered job"""

    name: str
    description: str | None
    trigger_type: TriggerType
    is_active: bool
    cron_expression: str | None
    next_run_at: datetime | None

    # Source info
    process_typing: TypingRefDTO | None
    scenario_template_id: str | None
    scenario_template_name: str | None

    # Configuration
    config_values: dict | None

    # Last run info (convenience)
    last_run: TriggeredJobRunDTO | None


class TriggeredJobSimpleDTO(ModelDTO):
    """Simplified DTO for triggered job (for lists)"""

    name: str
    trigger_type: TriggerType
    is_active: bool
    cron_expression: str | None
    next_run_at: datetime | None
    last_status: JobStatus | None


# === CREATE DTOs ===


class CreateTriggeredJobFromProcessDTO(BaseModelDTO):
    """DTO for creating a job from a Task/Protocol typing"""

    process_typing_name: str
    name: str
    description: str | None = None
    cron_expression: str
    config_values: dict | None = None
    is_active: bool = False


class CreateTriggeredJobFromTemplateDTO(BaseModelDTO):
    """DTO for creating a job from a ScenarioTemplate"""

    scenario_template_id: str
    name: str
    description: str | None = None
    cron_expression: str
    config_values: dict | None = None
    is_active: bool = False


# === UPDATE DTOs ===


class UpdateTriggeredJobDTO(BaseModelDTO):
    """DTO for updating a triggered job"""

    name: str | None = None
    description: str | None = None
    cron_expression: str | None = None
    config_values: dict | None = None


class ActivateTriggeredJobDTO(BaseModelDTO):
    """DTO for activating a triggered job"""

    cron_expression: str | None = None  # Optional: override the cron expression

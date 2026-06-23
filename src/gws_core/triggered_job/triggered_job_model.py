from datetime import datetime
from typing import TYPE_CHECKING

from croniter import croniter

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import (
    NullableCharField,
    NullableDateTimeUTC,
    NullableForeignKeyField,
    NullableJSONField,
    NullableTextField,
    TypedBooleanField,
    TypedCharField,
    TypedEnumField,
)
from gws_core.core.utils.date_helper import DateHelper
from gws_core.model.typing import Typing
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.triggered_job.triggered_job_types import (
    JobStatus,
    TriggerType,
)

if TYPE_CHECKING:
    from gws_core.triggered_job.triggered_job_run_model import TriggeredJobRunModel


class TriggeredJobModel(ModelWithUser):
    """
    Model for a triggered job configuration.

    A triggered job can execute a Task, Protocol, or ScenarioTemplate
    based on a trigger (CRON schedule or WEBHOOK call).
    """

    # === SOURCE OF THE SCENARIO ===
    # Option 1: Task or Protocol typing (mutually exclusive with scenario_template)
    process_typing = NullableForeignKeyField(Typing, backref="+")

    # Option 2: ScenarioTemplate (mutually exclusive with process_typing)
    scenario_template = NullableForeignKeyField(
        ScenarioTemplate, backref="triggered_jobs", on_delete="SET NULL"
    )

    # Configuration values for the process/template
    config_values = NullableJSONField()

    # === TRIGGER CONFIGURATION ===
    trigger_type = TypedEnumField(choices=TriggerType)

    # CRON configuration
    cron_expression = NullableCharField(max_length=100)
    next_run_at = NullableDateTimeUTC()

    # === STATE ===
    is_active = TypedBooleanField(default=False)

    # === METADATA ===
    name = TypedCharField(max_length=255)
    description = NullableTextField()

    class Meta:
        table_name = "gws_triggered_job"
        is_table = True

    def is_cron_job(self) -> bool:
        """Check if this is a CRON triggered job"""
        return self.trigger_type == TriggerType.CRON

    def uses_process_typing(self) -> bool:
        """Check if this job uses a Task/Protocol typing"""
        return self.process_typing is not None

    def uses_scenario_template(self) -> bool:
        """Check if this job uses a ScenarioTemplate"""
        return self.scenario_template is not None

    def get_last_run(self) -> "TriggeredJobRunModel | None":
        """Get the last run of this job"""
        from gws_core.triggered_job.triggered_job_run_model import TriggeredJobRunModel

        return (
            TriggeredJobRunModel.select()
            .where(TriggeredJobRunModel.triggered_job == self)
            .order_by(TriggeredJobRunModel.started_at.desc())
            .first()
        )

    def get_last_status(self) -> JobStatus | None:
        """Get the status of the last run"""
        last_run = self.get_last_run()
        return last_run.status if last_run else None

    def is_running(self) -> bool:
        """Check if a run is currently in progress"""
        last_run = self.get_last_run()
        return last_run is not None and last_run.status == JobStatus.RUNNING

    def calculate_next_run(self) -> datetime | None:
        """Calculate the next run time based on cron_expression"""
        if not self.cron_expression:
            return None

        try:
            cron = croniter(self.cron_expression, DateHelper.now_utc())
            return cron.get_next(datetime)
        except Exception:
            return None

    def update_next_run(self) -> None:
        """Update next_run_at based on cron_expression"""
        if self.is_active and self.is_cron_job():
            self.next_run_at = self.calculate_next_run()
        else:
            self.next_run_at = None

    @classmethod
    def get_active_cron_jobs_to_run(cls, now: datetime) -> list["TriggeredJobModel"]:
        """Get all active CRON jobs that should run (next_run_at <= now)"""
        return list(
            cls.select().where(
                (cls.is_active == True)
                & (cls.trigger_type == TriggerType.CRON)
                & (cls.next_run_at <= now)
                & (cls.next_run_at.is_null(False))
            )
        )

    @classmethod
    def get_by_process_typing(cls, typing: Typing) -> "TriggeredJobModel | None":
        """Get a job by its process typing"""
        return cls.get_or_none(cls.process_typing == typing)

    @classmethod
    def get_by_process_typing_name(cls, typing_name: str) -> "TriggeredJobModel | None":
        """Get a job by its process typing name"""
        typing = Typing.get_by_typing_name(typing_name)
        if typing is None:
            return None
        return cls.get_by_process_typing(typing)

    @classmethod
    def get_all_active_jobs(cls) -> list["TriggeredJobModel"]:
        """Get all active jobs"""
        return list(cls.select().where(cls.is_active == True))

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_by_id(cls, id_: str) -> None:
        """Delete a job by its ID"""
        job = cls.get_by_id_and_check(id_)

        # Delete associated runs first
        from gws_core.triggered_job.triggered_job_run_model import TriggeredJobRunModel

        TriggeredJobRunModel.delete().where(TriggeredJobRunModel.triggered_job == job).execute()

        job.delete_instance()

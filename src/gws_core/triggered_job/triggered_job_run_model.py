from datetime import datetime

from peewee import ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import DateTimeUTC, JSONField
from gws_core.core.model.model import Model
from gws_core.core.utils.date_helper import DateHelper
from gws_core.scenario.scenario import Scenario
from gws_core.triggered_job.triggered_job_model import TriggeredJobModel
from gws_core.triggered_job.triggered_job_types import JobRunTrigger, JobStatus


class TriggeredJobRunModel(Model):
    """
    Model for tracking individual runs of a triggered job.

    Each time a TriggeredJob is executed, a new TriggeredJobRunModel is created
    to track the execution status and link to the created scenario.
    """

    # Reference to the parent job
    triggered_job: TriggeredJobModel = ForeignKeyField(
        TriggeredJobModel, backref="runs", null=False, on_delete="CASCADE"
    )

    # How the job was triggered
    trigger: JobRunTrigger = EnumField(choices=JobRunTrigger, null=False)

    # The scenario that was created and executed
    scenario: Scenario = ForeignKeyField(
        Scenario, null=True, backref="triggered_job_runs", on_delete="SET NULL"
    )

    # Timing
    started_at: datetime = DateTimeUTC(null=False, default=DateHelper.now_utc)
    ended_at: datetime = DateTimeUTC(null=True)

    # Execution status
    status: JobStatus = EnumField(choices=JobStatus, null=False)

    # Error information if status is ERROR
    # Format: {"message": str, "stacktrace": str}
    error_info: dict = JSONField(null=True)

    class Meta:
        table_name = "gws_triggered_job_run"
        is_table = True

    def is_running(self) -> bool:
        """Check if this run is still in progress"""
        return self.status == JobStatus.RUNNING

    def is_success(self) -> bool:
        """Check if this run completed successfully"""
        return self.status == JobStatus.SUCCESS

    def is_error(self) -> bool:
        """Check if this run failed"""
        return self.status == JobStatus.ERROR

    def mark_as_success(self) -> "TriggeredJobRunModel":
        """Mark this run as successful"""
        self.status = JobStatus.SUCCESS
        self.ended_at = DateHelper.now_utc()
        self.save()
        return self

    def mark_as_error(self, message: str, stacktrace: str | None = None) -> "TriggeredJobRunModel":
        """Mark this run as failed"""
        self.status = JobStatus.ERROR
        self.ended_at = DateHelper.now_utc()
        self.error_info = {
            "message": message,
            "stacktrace": stacktrace,
        }
        self.save()
        return self

    def get_duration_seconds(self) -> float | None:
        """Get the duration of this run in seconds"""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    @classmethod
    def get_runs_for_job(
        cls, job: TriggeredJobModel, limit: int = 100
    ) -> list["TriggeredJobRunModel"]:
        """Get all runs for a specific job, ordered by most recent first"""
        return list(
            cls.select()
            .where(cls.triggered_job == job)
            .order_by(cls.started_at.desc())
            .limit(limit)
        )

    @classmethod
    def get_running_runs(cls) -> list["TriggeredJobRunModel"]:
        """Get all currently running job runs"""
        return list(cls.select().where(cls.status == JobStatus.RUNNING))

    @classmethod
    def create_run(
        cls,
        triggered_job: TriggeredJobModel,
        trigger: JobRunTrigger,
    ) -> "TriggeredJobRunModel":
        """Create a new run entry in RUNNING status"""
        run = cls(
            triggered_job=triggered_job,
            trigger=trigger,
            status=JobStatus.RUNNING,
            started_at=DateHelper.now_utc(),
        )
        run.save()
        return run

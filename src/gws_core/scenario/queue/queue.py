from typing import Optional, Union

from peewee import ForeignKeyField, ModelSelect

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions import BadRequestException
from gws_core.core.model.model import Model
from gws_core.scenario.queue.queue_dto import JobDTO
from gws_core.scenario.scenario import Scenario
from gws_core.user.user import User

MAX_QUEUE_LENGTH = 10


class Job(Model):
    """
    Class representing queue job

    :property user: The user who creates the job
    :type user: `gws.user.User`
    :property scenario: The scenario to add to the job
    :type scenario: `gws.scenario.Scenario`
    """

    user: User = ForeignKeyField(User, null=False, backref="+")
    scenario: Scenario = ForeignKeyField(Scenario, null=False, backref="+", unique=True)

    @classmethod
    @GwsCoreDbManager.transaction(
        nested_transaction=True
    )  # use nested to prevent transaction block in queue tick (from parent call)
    def add_job(cls, user: User, scenario: Scenario) -> "Job":
        """Validate and add a job to the queue."""
        if cls.scenario_in_queue(scenario.id):
            raise BadRequestException("The scenario already is in the queue")

        if cls.queue_length() >= MAX_QUEUE_LENGTH:
            raise BadRequestException("The maximum number of jobs is reached")

        scenario.mark_as_in_queue()
        job = Job(user=user, scenario=scenario)
        job.save()

        return job

    @classmethod
    @GwsCoreDbManager.transaction(
        nested_transaction=True
    )  # use nested to prevent transaction block in queue tick (from parent call)
    def remove_scenario(cls, scenario_id: str) -> Scenario:
        """Remove a scenario from the queue and reset to DRAFT."""
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        if scenario.status != scenario.status.IN_QUEUE:
            raise BadRequestException("The scenario does not have the queued status")

        scenario.mark_as_draft()
        cls.remove_scenario_from_queue(scenario_id)
        return scenario

    @classmethod
    def pop_first(cls) -> Optional["Job"]:
        """Pop the first job from the queue."""
        job = cls._get_jobs_in_order().first()
        if job is not None:
            cls.delete_by_id(job.id)
        return job

    @classmethod
    def get_all_jobs(cls) -> list["Job"]:
        """Get all jobs in the queue ordered by creation time."""
        return list(cls._get_jobs_in_order())

    @classmethod
    def _get_jobs_in_order(cls) -> ModelSelect:
        return Job.select().order_by(cls.created_at.asc())

    @classmethod
    def queue_length(cls) -> int:
        """Get the number of jobs in the queue."""
        return Job.select().count()

    @classmethod
    def scenario_in_queue(cls, scenario_id: str) -> bool:
        """Check if a scenario is already in the queue."""
        return Job.select().where(cls.scenario == scenario_id).count() > 0

    @classmethod
    def remove_scenario_from_queue(cls, scenario_id: str) -> None:
        """Remove a scenario's job entry from the queue."""
        return Job.delete().where(cls.scenario == scenario_id).execute()

    def to_dto(self) -> JobDTO:
        return JobDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            user=self.user.to_dto(),
            scenario=self.scenario.to_dto(),
        )

    class Meta:
        table_name = "gws_queue_job"
        is_table = True

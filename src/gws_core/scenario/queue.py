

from typing import List, Optional, Union

from gws_core.core.decorator.transaction import transaction
from gws_core.scenario.queue_dto import JobDTO
from peewee import BooleanField, ForeignKeyField, IntegerField, ModelSelect

from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..user.user import User
from .scenario import Scenario


class Queue(Model):
    """
    Singleton Class representing scenario queue

    :property is_active: True is the queue is active; False otherwise. Defaults to False.
    The queue is automatically set to True on init.
    :type is_active: `bool`
    :property max_length: The maximum length of the queue. Defaults to 10.
    :type max_length: `int`
    """

    is_active = BooleanField(default=False)
    max_length = IntegerField(default=10)

    _current_queue: 'Queue' = None

    @classmethod
    def get_current_queue(cls) -> Optional['Queue']:
        return cls._current_queue

    @classmethod
    @transaction(nested_transaction=True)  # force new transaction to commit anyway
    def _get_or_create_instance(cls) -> 'Queue':
        if cls._current_queue is None:
            queue = Queue.select().first()
            if queue is not None:
                cls._current_queue = queue
            else:
                cls._current_queue = Queue().save()

        return cls._current_queue

    @classmethod
    def init(cls) -> 'Queue':
        queue = cls._get_or_create_instance()
        if not queue.is_active:
            queue.is_active = True
            queue.save()
            Logger.info("The queue is initialized and active")

        return queue

    @classmethod
    def deinit(cls):
        if not cls.table_exists():
            return
        queue = cls.get_current_queue()

        if queue is not None:
            cls.delete_by_id(queue.id)
            cls._current_queue = None

    @classmethod
    @transaction(nested_transaction=True)  # use nested to prevent transaction block in queue tick (from parent call)
    def add_job(cls, user: User, scenario: Scenario) -> 'Queue':

        if Job.scenario_in_queue(scenario.id):
            raise BadRequestException("The scenario already is in the queue")

        queue = cls._get_or_create_instance()
        if Job.count_scenario_in_queue(queue.id) > queue.max_length:
            raise BadRequestException("The maximum number of jobs is reached")

        scenario.mark_as_in_queue()
        job = Job(user=user, scenario=scenario, queue=queue)
        job.save()

        return queue

    @classmethod
    @transaction(nested_transaction=True)  # use nested to prevent transaction block in queue tick (from parent call)
    def remove_scenario(cls, scenario_id: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        if scenario.status != scenario.status.IN_QUEUE:
            raise BadRequestException('The scenario does not have the queued status')

        scenario.mark_as_draft()
        Job.remove_scenario_from_queue(scenario_id)
        return scenario

    @classmethod
    def length(cls) -> int:
        return Job.select().count()

    @classmethod
    def pop_first(cls) -> Optional['Job']:
        queue = cls.get_current_queue()

        if not queue:
            return None

        return Job.pop_first_job(queue.id)

    @classmethod
    def get_jobs(cls) -> List['Job']:
        queue = cls.get_current_queue()

        if not queue:
            return []

        return Job.get_queue_jobs(queue.id)

    class Meta:
        table_name = 'gws_queue'
        is_table = True


class Job(Model):
    """
    Class representing queue job

    :property user: The user who creates the job
    :type user: `gws.user.User`
    :property scenario: The scenario to add to the job
    :type scenario: `gws.scenario.Scenario`
    """

    user: User = ForeignKeyField(User, null=False, backref='+')
    scenario: Scenario = ForeignKeyField(Scenario, null=False, backref='+', unique=True)
    queue: Queue = ForeignKeyField(Queue, null=False, backref='+')

    @classmethod
    def pop_first_job(cls, queue_id: str) -> Union['Job', None]:
        job = cls.get_first_job(queue_id)

        if job is not None:
            cls.delete_by_id(job.id)

        return job

    @classmethod
    def get_first_job(cls, queue_id: str) -> Union['Job', None]:
        return cls._get_job_in_orders(queue_id).first()

    @classmethod
    def get_queue_jobs(cls, queue_id: str) -> List['Job']:
        return list(cls._get_job_in_orders(queue_id))

    @classmethod
    def _get_job_in_orders(cls, queue_id: str) -> ModelSelect:
        return Job.select().where(cls.queue == queue_id).order_by(cls.created_at.asc())

    @classmethod
    def count_scenario_in_queue(cls, queue_id: str) -> int:
        return Job.select().where(cls.queue == queue_id).count()

    @classmethod
    def scenario_in_queue(cls, scenario_id: str) -> bool:
        return Job.select().where(cls.scenario == scenario_id).count() > 0

    @classmethod
    def remove_scenario_from_queue(cls, scenario_id: str) -> None:
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
        table_name = 'gws_queue_job'
        is_table = True

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional, Union

from peewee import BooleanField, ForeignKeyField, IntegerField, ModelSelect

from gws_core.core.decorator.transaction import transaction
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.experiment.queue_dto import JobDTO

from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..user.user import User
from .experiment import Experiment


class Queue(Model):
    """
    Singleton Class representing experiment queue

    :property is_active: True is the queue is active; False otherwise. Defaults to False.
    The queue is automatically set to True on init.
    :type is_active: `bool`
    :property max_length: The maximum length of the queue. Defaults to 10.
    :type max_length: `int`
    """

    is_active = BooleanField(default=False)
    max_length = IntegerField(default=10)

    _current_queue: 'Queue' = None
    _table_name = "gws_queue"

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
        queue = cls.get_current_queue()

        if queue is not None:
            cls.delete_by_id(queue.id)
            cls._current_queue = None

    @classmethod
    @transaction(nested_transaction=True)  # use nested to prevent transaction block in queue tick (from parent call)
    def add_job(cls, user: User, experiment: Experiment) -> 'Queue':

        if Job.experiment_in_queue(experiment.id):
            raise BadRequestException("The experiment already is in the queue")

        queue = cls._get_or_create_instance()
        if Job.count_experiment_in_queue(queue.id) > queue.max_length:
            raise BadRequestException("The maximum number of jobs is reached")

        experiment.mark_as_in_queue()
        job = Job(user=user, experiment=experiment, queue=queue)
        job.save()

        return queue

    @classmethod
    @transaction(nested_transaction=True)  # use nested to prevent transaction block in queue tick (from parent call)
    def remove_experiment(cls, experiment_id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        if experiment.status != experiment.status.IN_QUEUE:
            raise BadRequestException('The experiment does not have the queued status')

        experiment.mark_as_draft()
        Job.remove_experiment_from_queue(experiment_id)
        return experiment

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


class Job(Model):
    """
    Class representing queue job

    :property user: The user who creates the job
    :type user: `gws.user.User`
    :property experiment: The experiment to add to the job
    :type experiment: `gws.experiment.Experiment`
    """

    user: User = ForeignKeyField(User, null=False, backref='+')
    experiment: Experiment = ForeignKeyField(Experiment, null=False, backref='+', unique=True)
    queue: Queue = ForeignKeyField(Queue, null=False, backref='+')
    _table_name = "gws_queue_job"

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
    def count_experiment_in_queue(cls, queue_id: str) -> int:
        return Job.select().where(cls.queue == queue_id).count()

    @classmethod
    def experiment_in_queue(cls, experiment_id: str) -> bool:
        return Job.select().where(cls.experiment == experiment_id).count() > 0

    @classmethod
    def remove_experiment_from_queue(cls, experiment_id: str) -> None:
        return Job.delete().where(cls.experiment == experiment_id).execute()

    def to_dto(self) -> JobDTO:
        return JobDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            user=self.user.to_dto(),
            experiment=self.experiment.to_dto(),
        )

    class Meta:
        table_name = 'gws_queue_job'

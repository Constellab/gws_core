# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Union

from gws_core.core.decorator.transaction import transaction
from peewee import BooleanField, ForeignKeyField, IntegerField, ModelSelect

from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..model.typing_register_decorator import typing_registrator
from ..user.user import User
from .experiment import Experiment


@typing_registrator(unique_name="Queue", object_type="MODEL", hide=True)
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
    _queue_instance = None
    _table_name = "gws_queue"
    _instance: 'Queue' = None

    @classmethod
    def get_instance(cls) -> 'Queue':
        if cls._instance is None:
            queue = Queue.select().first()
            if queue is not None:
                cls._instance = queue
            else:
                cls._instance = Queue().save()

        return cls._instance

    @classmethod
    def init(cls) -> 'Queue':
        queue = cls.get_instance()
        if not queue.is_active:
            queue.is_active = True
            queue.save()
            Logger.info("The queue is initialized and active")

        return queue

    @classmethod
    def deinit(cls):
        queue = cls.get_instance()
        queue.is_active = False
        queue.save()

    @classmethod
    @transaction()
    def add_job(cls, user: User, experiment: Experiment) -> 'Queue':

        if Job.experiment_in_queue(experiment.id):
            raise BadRequestException("The experiment already is in the queue")

        queue = cls.get_instance()
        if Job.count_experiment_in_queue(queue.id) > queue.max_length:
            raise BadRequestException("The maximum number of jobs is reached")

        experiment.mark_as_in_queue()
        job = Job(user=user, experiment=experiment, queue=queue)
        job.save()

        return queue

    @classmethod
    @transaction()
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
    def pop_first(cls) -> 'Job':
        queue = cls.get_instance()

        return Job.pop_first_job(queue.id)

    @classmethod
    def get_jobs(cls) -> 'Job':
        queue = Queue.get_instance()
        return Job.get_queue_jobs(queue.id)


@typing_registrator(unique_name="Job", object_type="MODEL", hide=True)
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

    def to_json(self, deep: bool) -> Dict:

        json_ = super().to_json(deep=deep)
        json_["user"] = self.user.to_json()
        json_["experiment"] = self.experiment.to_json()
        return json_

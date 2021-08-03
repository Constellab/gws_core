# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from peewee import BooleanField, ForeignKeyField, IntegerField

from ..core.exception import BadRequestException
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..user.user import User
from .experiment import Experiment


class Job(Model):
    """
    Class representing queue job

    :property user: The user who creates the job
    :type user: `gws.user.User`
    :property experiment: The experiment to add to the job
    :type experiment: `gws.experiment.Experiment`
    """

    user = ForeignKeyField(User, null=True, backref='jobs')
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')
    _table_name = "gws_queue_job"


class Queue(Model):
    """
    Class representing experiment queue

    :property is_active: True is the queue is active; False otherwise. Defaults to False.
    The queue is automatically set to True on init.
    :type is_active: `bool`
    :property max_length: The maximum length of the queue. Defaults to 10.
    :type max_length: `int`
    """

    is_active = BooleanField(default=False)
    max_length = IntegerField(default=10)
    _queue_instance = None
    _is_singleton = True
    _table_name = "gws_queue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("jobs"):
            self.data["jobs"] = []
            self.save()

    @classmethod
    def init(cls) -> 'Queue':
        queue = Queue()
        if not queue.is_active:
            queue.is_active = True
            queue.save()
            Logger.info("The queue is initialized and active")

        return queue

    @classmethod
    def deinit(cls):
        queue = Queue()
        queue.is_active = False
        queue.save()

    # -- A --

    @classmethod
    def add(cls, job: Job) -> 'Queue':
        if not isinstance(job, Job):
            raise BadRequestException(
                "Invalid argument. An instance of gws.queue.Jobs is required")
        job.save()
        queue = Queue()
        if job.uri in queue.data["jobs"]:
            return
        if len(queue.data["jobs"]) > queue.max_length:
            raise BadRequestException("The maximum number of jobs is reached")
        queue.data["jobs"].append(job.uri)
        queue.save()

        return queue

    # -- G --

    # -- R --

    @classmethod
    def remove(cls, job: Job):
        if not isinstance(job, Job):
            raise BadRequestException(
                "Invalid argument. An instance of gws.queue.Job is required")
        queue = Queue()
        if job.uri in queue.data["jobs"]:
            queue.data["jobs"].remove(job.uri)
            queue.save()

    # -- L --

    @classmethod
    def length(cls):
        queue = Queue()
        return len(queue.data["jobs"])

    # -- N --

    @classmethod
    def next(cls) -> Job:
        queue = Queue()
        if not queue.data["jobs"]:
            return None
        uri = queue.data["jobs"][0]
        try:
            return Job.get(Job.uri == uri)
        except:
            # orphan job => discard it from the queue
            cls.pop_first()
            return cls.next()

    # -- P --

    @classmethod
    def pop_first(cls):
        queue = Queue()
        queue.data["jobs"].pop(0)
        queue.save()

    # -- S --

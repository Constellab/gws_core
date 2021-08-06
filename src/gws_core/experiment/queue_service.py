
import threading
import time

from ..core.exception.exceptions import BadRequestException, NotFoundException
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..user.current_user_service import CurrentUserService
from .experiment import Experiment
from .experiment_service import ExperimentService
from .queue import Job, Queue

TICK_INTERVAL_SECONDS = 30   # 30 sec


class QueueService(BaseService):
    # Bool to true during the tick method (used to prevent concurrent ticks)
    tick_is_running: bool = False
    is_init = False

    @classmethod
    def init(cls, tick_interval: int = TICK_INTERVAL_SECONDS, verbose=False, daemon=False):
        queue: Queue = Queue.init()
        if not cls.is_init or not queue.is_active:
            cls._queue_tick(tick_interval, verbose, daemon)
        cls.is_init = True

    @classmethod
    def deinit(cls):
        Queue.deinit()

    @classmethod
    def _queue_tick(cls, tick_interval, verbose, daemon):
        queue = Queue.get_instance()
        if not queue.is_active:
            return
        try:
            cls._tick(verbose)
        finally:
            thread = threading.Timer(tick_interval, cls._queue_tick, [
                tick_interval, verbose, daemon])
            thread.daemon = daemon
            thread.start()

    @classmethod
    def add_job(cls, job: Job, auto_start: bool = False):
        queue: Queue = Queue.add(job=job)
        if auto_start:
            if queue.is_active:
                # > manally trigger the experiment if possible!
                if not Experiment.count_of_running_experiments():
                    cls._tick()
            else:
                cls.init()

    @classmethod
    def _tick(cls, verbose=False):
        """Method called a each tick to run experiment from the queue

        :param verbose: [description], defaults to False
        :type verbose: bool, optional
        """
        if cls.tick_is_running:
            if verbose:
                Logger.info(
                    "Skipping queue tick, because previous one is running")
            return

        cls.tick_is_running = True

        try:
            cls._check_and_run_queue(verbose=verbose)
        finally:
            cls.tick_is_running = False

    @classmethod
    def _check_and_run_queue(cls, verbose):
        """Get the first experiment from the queue and run it if possible

        :param verbose: [description]
        :type verbose: [type]
        :raises BadRequestException: [description]
        """
        if verbose:
            Logger.info("Checking experiment queue ...")

        job = Queue.next()
        if not job:
            return

        # tester que l'experiment est bien à jour
        experiment: Experiment = job.experiment

        if verbose:
            Logger.info(
                f"Experiment {experiment.uri}, is_running = {experiment.is_running}")

        if Experiment.count_of_running_experiments():
            # -> busy: we will test later!
            if verbose:
                Logger.info("The lab is busy! Retry later")
            return

        if verbose:
            Logger.info(
                f"Start experiment {experiment.uri}, user={job.user.uri}")

        try:
            ExperimentService.run_through_cli(
                experiment=experiment, user=job.user)
        except Exception as err:
            raise BadRequestException(
                f"An error occured while runnig the experiment. Error: {err}.") from err
        finally:
            # Remove the experiment from the queue before executing it
            Queue.pop_first()

    @classmethod
    def add_experiment_to_queue(cls, experiment_uri: str) -> Experiment:
        """Add the experiment to the queue and run it when ready


        :param uri: [description]
        :type uri: [type]
        :raises NotFoundException: [description]
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Experiment
        """

        # todo check if the experiment is already in the queue.
        experiment: Experiment = None
        try:
            experiment = Experiment.get(Experiment.uri == experiment_uri)
        except Exception as err:
            raise NotFoundException(
                detail=f"Experiment '{experiment_uri}' is not found") from err

        # check experiment status
        experiment.check_is_runnable()

        try:
            user = CurrentUserService.get_and_check_current_user()
            job = Job(user=user, experiment=experiment)
            cls.add_job(job, auto_start=True)
            return experiment
        except Exception as err:
            raise BadRequestException(detail="An error occured.") from err

    @classmethod
    def get_queue(cls) -> 'Queue':
        queue = Queue.get_instance()
        return queue

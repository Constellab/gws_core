
import threading

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException

from ..core.exception.exceptions import NotFoundException
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..experiment.experiment_run_service import ExperimentRunService
from ..user.current_user_service import CurrentUserService
from .experiment import Experiment, ExperimentStatus
from .queue import Job, Queue

TICK_INTERVAL_SECONDS = 30   # 30 sec


class QueueService(BaseService):
    # Bool to true during the tick method (used to prevent concurrent ticks)
    tick_is_running: bool = False
    is_init = False

    @classmethod
    def init(cls, tick_interval: int = TICK_INTERVAL_SECONDS, daemon=False) -> None:
        queue: Queue = Queue.init()
        if not cls.is_init or not queue.is_active:
            cls._queue_tick(tick_interval, daemon)
        cls.is_init = True

    @classmethod
    def deinit(cls) -> None:
        if not cls.is_init:
            return
        Queue.deinit()
        cls.is_init = False

    @classmethod
    def _queue_tick(cls, tick_interval, daemon):
        queue = Queue.get_instance()
        if not queue.is_active:
            return
        try:
            cls._tick()
        finally:
            thread = threading.Timer(tick_interval, cls._queue_tick, [
                tick_interval, daemon])
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
    def _tick(cls):
        """Method called a each tick to run experiment from the queue

        :param verbose: [description], defaults to False
        :type verbose: bool, optional
        """
        if cls.tick_is_running:
            Logger.debug(
                "Skipping queue tick, because previous one is running")
            return

        cls.tick_is_running = True

        try:
            cls._check_and_run_queue()
        finally:
            cls.tick_is_running = False

    @classmethod
    def _check_and_run_queue(cls):
        """Get the first experiment from the queue and run it if possible

        :param verbose: [description]
        :type verbose: [type]
        :raises BadRequestException: [description]
        """
        Logger.debug("Checking experiment queue ...")

        job = Queue.next()
        if not job:
            return

        # tester que l'experiment est bien à jour
        experiment: Experiment = job.experiment

        Logger.debug(
            f"Experiment {experiment.id}, is_running = {experiment.is_running}")

        if Experiment.count_of_running_experiments():
            # -> busy: we will test later!
            Logger.debug("The lab is busy! Retry later")
            return

        try:
            ExperimentRunService.create_cli_process_for_experiment(
                experiment=experiment, user=job.user)
        except Exception as err:
            Logger.error(
                f"An error occured while runnig the experiment. Error: {err}.")
            raise err

        finally:
            # Remove the experiment from the queue before executing it
            Queue.pop_first()

    @classmethod
    def add_experiment_to_queue(cls, experiment_id: str) -> Experiment:
        """Add the experiment to the queue and run it when ready


        :param id: [description]
        :type id: [type]
        :raises NotFoundException: [description]
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Experiment
        """

        # todo check if the experiment is already in the queue.
        experiment: Experiment = None
        try:
            experiment = Experiment.get(Experiment.id == experiment_id)
        except Exception as err:
            raise NotFoundException(
                detail=f"Experiment '{experiment_id}' is not found") from err

        # check experiment status
        experiment.check_is_runnable()

        if experiment.status != ExperimentStatus.DRAFT:
            Logger.info(f"Resetting experiment {experiment.id} before adding it to the queue")

            try:
                experiment.reset()
            except BaseHTTPException as err:
                raise err
            except Exception as err:
                # printing stack trace
                Logger.log_exception_stack_trace(err)
                raise BadRequestException(
                    f"Error while resetting experiment {experiment.id} before adding it to the queue")

        user = CurrentUserService.get_and_check_current_user()
        job = Job(user=user, experiment=experiment)
        cls.add_job(job, auto_start=True)
        return experiment

    @classmethod
    def get_queue(cls) -> 'Queue':
        queue = Queue.get_instance()
        return queue

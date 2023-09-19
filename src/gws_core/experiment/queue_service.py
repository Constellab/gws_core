# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import threading
from typing import List

from gws_core.core.model.sys_proc import SysProc
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.user.user import User

from ..core.exception.exceptions import NotFoundException
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..experiment.experiment_run_service import ExperimentRunService
from ..user.current_user_service import CurrentUserService
from .experiment import Experiment, ExperimentStatus
from .queue import Job, Queue

TICK_INTERVAL_SECONDS = 60   # 60 sec


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
        queue = Queue.get_current_queue()
        if not queue or not queue.is_active:
            return
        try:
            cls._tick()
        finally:
            thread = threading.Timer(tick_interval, cls._queue_tick, [
                tick_interval, daemon])
            thread.daemon = daemon
            thread.start()

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
        if Experiment.count_running_experiments() > 0:
            # -> busy: we will test later!
            Logger.debug("The lab is busy! Retry later")
            return

        job = Queue.pop_first()
        if not job:
            return

        # tester que l'experiment est bien à jour
        experiment: Experiment = job.experiment

        Logger.debug(
            f"Experiment {experiment.id}, is_running = {experiment.is_running}")

        try:
            sproc = ExperimentRunService.create_cli_for_experiment(
                experiment=experiment, user=job.user)

            if sproc:
                # wait for the experiment to finish in a separate thread
                thread = threading.Thread(
                    target=cls._wait_experiment_finish, args=(sproc,))
                thread.start()
        except Exception as err:
            Logger.error(
                f"An error occured while runnig the experiment. Error: {err}.")
            raise err

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

        experiment: Experiment = None
        try:
            experiment = Experiment.get(Experiment.id == experiment_id)
        except Exception as err:
            raise NotFoundException(
                detail=f"Experiment '{experiment_id}' is not found") from err

        if Job.experiment_in_queue(experiment.id):
            raise BadRequestException("The experiment already is in the queue")

        # check experiment status
        experiment.check_is_runnable()

        if experiment.is_running or experiment.status == ExperimentStatus.IN_QUEUE:
            raise BadRequestException(
                "The experiment is already running or in the queue")

        # reset the processes that are in error
        ProtocolService.reset_error_processes_of_protocol(
            experiment.protocol_model)

        user = CurrentUserService.get_and_check_current_user()
        cls._add_job(user=user, experiment=experiment, auto_start=True)
        return experiment

    @classmethod
    def _add_job(cls, user: User, experiment: Experiment, auto_start: bool = False):
        queue: Queue = Queue.add_job(user=user, experiment=experiment)
        if auto_start:
            if queue.is_active:
                # > manally trigger the experiment if possible!
                if not Experiment.count_running_experiments():
                    cls._tick()
            else:
                cls.init()

    @classmethod
    def get_queue_jobs(cls) -> List[Job]:
        return Queue.get_jobs()

    @classmethod
    def _wait_experiment_finish(cls, proc: SysProc):
        proc.wait()
        # force a tick to run the next experiment if possible
        cls._tick()

    @classmethod
    def experiment_is_in_queue(cls, experiment_id: str) -> bool:
        return Job.experiment_in_queue(experiment_id)

    @classmethod
    def remove_experiment_from_queue(cls, experiment_id: str) -> Experiment:
        return Queue.remove_experiment(experiment_id)

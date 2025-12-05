import threading

from gws_core.core.model.sys_proc import SysProc
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.user.user import User

from ..core.exception.exceptions import NotFoundException
from ..core.exception.exceptions.bad_request_exception import BadRequestException
from ..core.utils.logger import Logger
from ..user.current_user_service import AuthenticateUser, CurrentUserService
from .queue import Job, Queue
from .scenario import Scenario, ScenarioStatus
from .scenario_run_service import ScenarioRunService

TICK_INTERVAL_SECONDS = 60  # 60 sec


class QueueService:
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
            thread = threading.Timer(tick_interval, cls._queue_tick, [tick_interval, daemon])
            thread.daemon = daemon
            thread.start()

    @classmethod
    def _tick(cls):
        """Method called a each tick to run scenario from the queue

        :param verbose: [description], defaults to False
        :type verbose: bool, optional
        """
        if cls.tick_is_running:
            Logger.debug("Skipping queue tick, because previous one is running")
            return

        cls.tick_is_running = True

        try:
            cls._check_and_run_queue()
        finally:
            cls.tick_is_running = False

    @classmethod
    def _check_and_run_queue(cls):
        """Get the first scenario from the queue and run it if possible

        :param verbose: [description]
        :type verbose: [type]
        :raises BadRequestException: [description]
        """
        Logger.debug("Checking scenario queue ...")
        if Scenario.count_running_scenarios() > 0:
            # -> busy: we will test later!
            Logger.debug("The lab is busy! Retry later")
            return

        job = Queue.pop_first()
        if not job:
            return

        # tester que l'scenario est bien à jour
        scenario: Scenario = job.scenario

        Logger.debug(f"Scenario {scenario.id}, is_running = {scenario.is_running}")

        try:
            with AuthenticateUser(job.user):
                sproc = ScenarioRunService.create_cli_for_scenario(scenario=scenario, user=job.user)

            if sproc:
                # wait for the scenario to finish in a separate thread
                thread = threading.Thread(target=cls._wait_scenario_finish, args=(sproc,))
                thread.start()
        except Exception as err:
            Logger.error(f"An error occured while runnig the scenario. Error: {err}.")
            raise err

    @classmethod
    def add_scenario_to_queue(cls, scenario_id: str) -> Scenario:
        """Add the scenario to the queue and run it when ready


        :param id: [description]
        :type id: [type]
        :raises NotFoundException: [description]
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Scenario
        """

        scenario: Scenario = None
        try:
            scenario = Scenario.get(Scenario.id == scenario_id)
        except Exception as err:
            raise NotFoundException(detail=f"Scenario '{scenario_id}' is not found") from err

        if Job.scenario_in_queue(scenario.id):
            raise BadRequestException("The scenario already is in the queue")

        # check scenario status
        scenario.check_is_runnable()

        if scenario.is_running or scenario.status == ScenarioStatus.IN_QUEUE:
            raise BadRequestException("The scenario is already running or in the queue")

        # reset the processes that are in error
        EntityNavigatorService.reset_error_processes_of_protocol(scenario.protocol_model)

        user = CurrentUserService.get_and_check_current_user()
        cls._add_job(user=user, scenario=scenario, auto_start=True)
        return scenario

    @classmethod
    def _add_job(cls, user: User, scenario: Scenario, auto_start: bool = False):
        queue: Queue = Queue.add_job(user=user, scenario=scenario)
        if auto_start:
            if queue.is_active:
                # > manally trigger the scenario if possible!
                if not Scenario.count_running_scenarios():
                    cls._tick()
            else:
                cls.init()

    @classmethod
    def get_queue_jobs(cls) -> list[Job]:
        return Queue.get_jobs()

    @classmethod
    def _wait_scenario_finish(cls, proc: SysProc):
        proc.wait()
        # force a tick to run the next scenario if possible
        cls._tick()

    @classmethod
    def scenario_is_in_queue(cls, scenario_id: str) -> bool:
        return Job.scenario_in_queue(scenario_id)

    @classmethod
    def remove_scenario_from_queue(cls, scenario_id: str) -> Scenario:
        return Queue.remove_scenario(scenario_id)

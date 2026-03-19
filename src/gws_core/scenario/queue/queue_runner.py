import threading

from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.logger import Logger
from gws_core.scenario.queue.queue import Job
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.user.current_user_service import AuthenticateUser

TICK_INTERVAL_SECONDS = 60  # 60 sec


class QueueRunner:
    """Manages the queue tick loop and subprocess lifecycle.

    Only initialized in the main process. Responsible for polling the queue,
    popping jobs, and spawning CLI sub-processes to execute scenarios.
    """

    tick_is_running: bool = False
    _is_running: bool = False

    @classmethod
    def init(cls, tick_interval: int = TICK_INTERVAL_SECONDS, daemon: bool = False) -> None:
        """Start the queue tick loop. Only call from main process."""
        cls._is_running = True
        cls._queue_tick(tick_interval, daemon)

    @classmethod
    def deinit(cls) -> None:
        """Stop the queue tick loop."""
        cls._is_running = False

    @classmethod
    def _queue_tick(cls, tick_interval: int, daemon: bool) -> None:
        """Recursive timer-based tick."""
        if not cls._is_running:
            return
        try:
            cls._tick()
        finally:
            thread = threading.Timer(tick_interval, cls._queue_tick, [tick_interval, daemon])
            thread.daemon = daemon
            thread.start()

    @classmethod
    def try_run_next(cls) -> None:
        """Trigger an immediate tick if the runner is active.

        Called after a job is added to avoid waiting for the next scheduled tick.
        No-op in sub-processes where the runner is not running.
        """
        if cls._is_running:
            cls._tick()

    @classmethod
    def _tick(cls) -> None:
        """Guarded tick execution."""
        if cls.tick_is_running:
            Logger.debug("Skipping queue tick, because previous one is running")
            return

        cls.tick_is_running = True

        try:
            cls._check_and_run_queue()
        finally:
            cls.tick_is_running = False

    @classmethod
    def _check_and_run_queue(cls) -> None:
        """Pop first job and spawn CLI subprocess if no scenario is running."""
        Logger.debug("Checking scenario queue ...")
        if Scenario.count_running_scenarios() > 0:
            Logger.debug("The lab is busy! Retry later")
            return

        job = Job.pop_first()
        if not job:
            return

        scenario: Scenario = job.scenario

        Logger.debug(f"Scenario {scenario.id}, is_running = {scenario.is_running}")

        try:
            with AuthenticateUser(job.user):
                sproc = ScenarioRunService.create_cli_for_scenario(scenario=scenario, user=job.user)

            if sproc:
                thread = threading.Thread(target=cls._wait_scenario_finish, args=(sproc,))
                thread.start()
        except Exception as err:
            Logger.error(f"An error occured while runnig the scenario. Error: {err}.")
            raise err

    @classmethod
    def _wait_scenario_finish(cls, proc: SysProc) -> None:
        """Wait for a scenario subprocess to finish, then force a tick."""
        proc.wait()
        cls._tick()

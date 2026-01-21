import threading
import time

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.triggered_job.triggered_job_model import TriggeredJobModel
from gws_core.triggered_job.triggered_job_service import TriggeredJobService
from gws_core.triggered_job.triggered_job_types import JobRunTrigger


class TriggeredJobScheduler:
    """
    Background scheduler for executing CRON triggered jobs.

    Runs in a separate thread and checks every 60 seconds for jobs
    that need to be executed (where next_run_at <= now).
    """

    _thread: threading.Thread | None = None
    _running: bool = False

    # Check interval in seconds
    CHECK_INTERVAL = 60

    @classmethod
    def init(cls) -> None:
        """
        Initialize and start the scheduler thread.
        Should be called at server startup.
        """

        if cls._thread is not None and cls._thread.is_alive():
            Logger.warning("TriggeredJobScheduler is already running")
            return

        cls._running = True
        cls._thread = threading.Thread(
            target=cls._scheduler_loop,
            name="TriggeredJobScheduler",
            daemon=True,
        )
        cls._thread.start()

        Logger.info("TriggeredJobScheduler started")

    @classmethod
    def stop(cls) -> None:
        """
        Stop the scheduler thread.
        """
        if not cls._running:
            return

        cls._running = False

        if cls._thread is not None and cls._thread.is_alive():
            # Wait for thread to finish (max 5 seconds)
            cls._thread.join(timeout=5)

        cls._thread = None
        Logger.info("TriggeredJobScheduler stopped")

    @classmethod
    def is_running(cls) -> bool:
        """Check if the scheduler is running"""
        return cls._running and cls._thread is not None and cls._thread.is_alive()

    @classmethod
    def _scheduler_loop(cls) -> None:
        """
        Main scheduler loop.
        Runs continuously, checking for jobs to execute every CHECK_INTERVAL seconds.
        """
        Logger.info("TriggeredJobScheduler loop started")

        while cls._running:
            try:
                cls._check_and_run_jobs()
            except Exception as e:
                Logger.error(f"Error in TriggeredJobScheduler: {e}")
                Logger.log_exception_stack_trace(e)

            # Sleep for the check interval, but check _running periodically
            # to allow quick shutdown
            for _ in range(cls.CHECK_INTERVAL):
                if not cls._running:
                    break
                time.sleep(1)

        Logger.info("TriggeredJobScheduler loop ended")

    @classmethod
    def _check_and_run_jobs(cls) -> None:
        """
        Check for jobs that need to run and execute them.
        """
        now = DateHelper.now_utc()

        # Get all active CRON jobs that should run
        jobs_to_run = TriggeredJobModel.get_active_cron_jobs_to_run(now)

        if not jobs_to_run:
            return

        Logger.debug(f"Found {len(jobs_to_run)} triggered job(s) to run")

        for job in jobs_to_run:
            # Skip if job is already running
            if job.is_running():
                Logger.debug(f"Skipping job '{job.name}' - already running")
                continue

            try:
                Logger.info(f"Executing triggered job '{job.name}' (CRON: {job.cron_expression})")
                TriggeredJobService.execute_job(job, JobRunTrigger.CRON)
            except Exception as e:
                Logger.error(f"Error executing triggered job '{job.name}': {e}")
                Logger.log_exception_stack_trace(e)

    @classmethod
    def force_check(cls) -> None:
        """
        Force an immediate check for jobs to run.
        Useful for testing or manual triggers.
        """
        Logger.info("Forcing triggered job check")
        cls._check_and_run_jobs()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import traceback
from typing import Any, Coroutine, List

from gws_core.central.central_dto import SendExperimentFinishMailData
from gws_core.central.central_service import CentralService
from gws_core.core.service.front_service import FrontService

from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.sys_proc import SysProc
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..experiment.experiment_exception import ExperimentRunException
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment
from .experiment_enums import ExperimentStatus, ExperimentType


class ExperimentRunService():
    """Service used to run experiment
    """

    @classmethod
    async def run_experiment_in_cli(cls, experiment_id: str) -> None:
        """Method called by the cli sub process to run the experiment
        """
        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        try:
            if experiment.status != ExperimentStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the experiment {experiment.id} as its status was changed before process could run it")

        except Exception as err:
            error_text = GWSException.EXPERIMENT_ERROR_BEFORE_RUN.value + str(err)
            Logger.error(error_text)
            experiment.mark_as_error({"detail": error_text,
                                      "unique_code": GWSException.EXPERIMENT_ERROR_BEFORE_RUN.name,
                                      "context": None, "instance_id": None})
        await cls.run_experiment(experiment)

    @classmethod
    async def run_experiment(cls, experiment: Experiment) -> Coroutine[Any, Any, Experiment]:
        """
        Run the experiment
        """
        user = CurrentUserService.get_and_check_current_user()

        # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

        Logger.info(f"Running experiment : {experiment.id}")

        ActivityService.add(
            Activity.START,
            object_type=experiment.full_classname(),
            object_id=experiment.id,
            user=user
        )

        try:
            experiment.mark_as_started()

            await experiment.protocol_model.run()

            experiment.mark_as_success()

            cls._send_experiment_finished_mail(experiment)

            return experiment
        except Exception as err:
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error({"detail": exception.get_detail_with_args(), "unique_code": exception.unique_code,
                                      "context": exception.context, "instance_id": exception.instance_id})
            cls._send_experiment_finished_mail(experiment)

            raise exception

    @classmethod
    def create_cli_process_for_experiment(cls, experiment: Experiment, user: User):
        """
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        settings: Settings = Settings.retrieve()
        cwd_dir = settings.get_cwd()

        # set the user in the context to make the update works
        CurrentUserService.set_current_user(user)

        # check user privilege
        experiment.check_user_privilege(user)

        if experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the experiment {experiment.id}")

        cmd = [
            "python3",
            os.path.join(cwd_dir, "manage.py"),
            "--cli",
            "gws_core.cli.run_experiment",
            "--experiment-id", experiment.id,
            "--user-id", user.id
        ]

        if settings.is_test:
            cmd.append("--cli_test")

        cmd.append("--runmode")
        if settings.is_prod:
            cmd.append("prod")
        else:
            cmd.append("dev")

        try:
            sproc = SysProc.popen(
                cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # Mark that a process is created for the experiment, but it is not started yet
            experiment.mark_as_waiting_for_cli_process(sproc.pid)

            Logger.info(
                f"gws.experiment.Experiment run_through_cli {str(cmd)}")
            Logger.info(
                f"""The experiment logs are not shown in the console, because it is run in another linux process ({experiment.pid}).
                To view them check the logs marked as {Logger.get_sub_process_text()} in the today's log file : {Logger.get_file_path()}""")
        except Exception as err:
            traceback.print_exc()
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error({"detail": exception.get_detail_with_args(), "unique_code": exception.unique_code,
                                      "context": exception.context, "instance_id": exception.instance_id})
            raise exception

    @classmethod
    def stop_experiment(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_stopable()

        # try to kill the pid if possible
        try:
            if experiment.pid != 0:
                cls._kill_experiment_pid(experiment.pid)
        except Exception as err:
            Logger.error(str(err))

        ActivityService.add(
            Activity.STOP,
            object_type=experiment.full_classname(),
            object_id=experiment.id
        )

        experiment.mark_as_error({"detail": GWSException.EXPERIMENT_STOPPED_MANUALLY.value,
                                  "unique_code": GWSException.EXPERIMENT_STOPPED_MANUALLY.name,
                                  "context": None, "instance_id": None})

        return experiment

    @classmethod
    def _kill_experiment_pid(cls, experiment_pid: int) -> None:
        """
        Kill the experiment through HTTP context if it is running

        This is only possible if the experiment has been started through the cli
        """

        if not experiment_pid or experiment_pid == 0:
            raise BadRequestException(
                f"The experiment pid is {experiment_pid}")
        try:
            sproc = SysProc.from_pid(experiment_pid)
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {experiment_pid}). Error: {err}") from err

        # Don't kill if the process is already a zombie
        if sproc.is_zombie():
            return

        try:
            # Gracefully stops the experiment and exits!
            sproc.kill()
            sproc.wait()
        except Exception as err:
            raise BadRequestException(
                f"Cannot kill the experiment (pid = {experiment_pid}). Error: {err}") from err

    @classmethod
    def stop_all_running_experiment(cls) -> None:
        experiments: List[Experiment] = cls.get_all_running_experiments()
        for experiment in experiments:
            try:
                cls.stop_experiment(experiment.id)
            except Exception as err:
                Logger.error(f'Could not stop experiment {experiment.id}. {str(err)}')

    @classmethod
    def get_all_running_experiments(cls) -> List[Experiment]:
        return list(
            Experiment.select().where(
                (Experiment.status == ExperimentStatus.RUNNING) |
                (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)))

    @classmethod
    def _send_experiment_finished_mail(cls, experiment: Experiment) -> None:
        if not Settings.is_prod or experiment.type != ExperimentType.EXPERIMENT:
            return
        try:
            elapsed_time = experiment.protocol_model.progress_bar.get_elapsed_time()

            # if the experiment runned in under 5 minutes, don't send an email
            if elapsed_time < 60 * 5:
                return

            user: User = CurrentUserService.get_and_check_current_user()
            experiment_dto: SendExperimentFinishMailData = {
                "title": experiment.title,
                "status": experiment.status.value,
                "experiment_link": FrontService.get_experiment_url(experiment_id=experiment.id)
            }

            CentralService.send_experiment_finished_mail(user.id, experiment_dto)
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            Logger.error(f"Error while sending the experiment finished mail : {err}")

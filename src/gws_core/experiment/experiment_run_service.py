# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import traceback
from multiprocessing import Process
from typing import List

from gws_core.core.service.front_service import FrontService
from gws_core.process.process_exception import ProcessRunException
from gws_core.process.process_model import ProcessModel
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.space.mail_service import MailService
from gws_core.space.space_dto import SendExperimentFinishMailData
from gws_core.task.task_model import TaskModel
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)

from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.sys_proc import SysProc
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..experiment.experiment_exception import ExperimentRunException
from ..user.activity.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment
from .experiment_enums import ExperimentStatus


class ExperimentRunService():
    """Service used to run experiment
    """

    @classmethod
    def run_experiment_in_cli(cls, experiment_id: str) -> None:
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
            experiment.mark_as_error(ProcessErrorInfo(
                detail=error_text,
                unique_code=GWSException.EXPERIMENT_ERROR_BEFORE_RUN.name,
                context=None,
                instance_id=None))
        cls.run_experiment(experiment)

    @classmethod
    def run_experiment(cls, experiment: Experiment) -> Experiment:
        """
        Run the experiment
        """
        try:
            cls._check_experiment_before_start(experiment)

            experiment.mark_as_started(os.getpid())

            Logger.info(f"Running experiment : {experiment.id}")

            ActivityService.add(
                ActivityType.RUN_EXPERIMENT,
                object_type=ActivityObjectType.EXPERIMENT,
                object_id=experiment.id,
            )

            experiment.protocol_model.run()

            experiment = experiment.refresh()
            experiment.mark_as_success()

            cls._send_experiment_finished_mail(experiment)

            return experiment
        except Exception as err:
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            error = ProcessErrorInfo(detail=exception.get_detail_with_args(), unique_code=exception.unique_code,
                                     context=None, instance_id=exception.instance_id)
            experiment = experiment.refresh()
            experiment.mark_as_error(error)

            cls._send_experiment_finished_mail(experiment)
            raise exception

    @classmethod
    def run_experiment_process_in_cli(cls, experiment_id: str, protocol_model_id: str, process_name: str) -> None:
        """Method called by the cli sub process to run the experiment
        """
        try:
            experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

            protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
                protocol_model_id)

            process_model = protocol_model.get_process(process_name)

            if experiment.status != ExperimentStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the experiment {experiment.id} as its status was changed before process could run it")

            if process_model.status != ProcessStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the process {process_model.id} as its status was changed before process could run it")

        except Exception as err:
            error_text = GWSException.EXPERIMENT_ERROR_BEFORE_RUN.value + str(err)
            Logger.error(error_text)
            experiment.mark_as_error(ProcessErrorInfo(detail=error_text,
                                                      unique_code=GWSException.EXPERIMENT_ERROR_BEFORE_RUN.name,
                                                      context=None, instance_id=None))
        cls._run_experiment_process(experiment, protocol_model, process_name)

    @classmethod
    def _run_experiment_process(cls, experiment: Experiment, protocol_model: ProtocolModel,
                                process_instance_name: str) -> Experiment:
        try:

            process_model = protocol_model.get_process(process_instance_name)

            cls._check_experiment_before_start(experiment)

            if not protocol_model.process_is_ready(process_model):
                raise BadRequestException(
                    "The process cannot be run because it is not ready. Where the previous process run and are the inputs provided ?")

            Logger.info(
                f"Running experiment process : {experiment.id}, protocol: {protocol_model.id}, process: {process_instance_name}")

            ActivityService.add(
                ActivityType.RUN_PROCESS,
                object_type=ActivityObjectType.PROCESS,
                object_id=process_model.id,
            )

            experiment.mark_as_started(os.getpid())

            protocol_model.run_process(process_instance_name)
            protocol_model = protocol_model.refresh()
            protocol_model.refresh_status()

            return experiment

        except Exception as err:
            exception: ProcessRunException = ProcessRunException.from_exception(
                process_model=process_model, exception=err)

            process_model.mark_as_error_and_parent(exception)
            raise exception

    @classmethod
    def _check_experiment_before_start(cls, experiment: Experiment) -> None:
        user = CurrentUserService.get_and_check_current_user()

        # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

    @classmethod
    def create_cli_for_experiment(cls, experiment: Experiment, user: User) -> SysProc:
        """
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        try:
            return cls._create_cli(experiment, user)
        except Exception as err:
            traceback.print_exc()
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error(ProcessErrorInfo(detail=exception.get_detail_with_args(),
                                                      unique_code=exception.unique_code,
                                                      context=None, instance_id=exception.instance_id))
            raise exception

    @classmethod
    def create_cli_for_experiment_process(cls, experiment: Experiment,
                                          protocol_model: ProtocolModel,
                                          process_instance_name: str,
                                          user: User) -> SysProc:
        """
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        process_model = protocol_model.get_process(process_instance_name)

        if not protocol_model.process_is_ready(process_model):
            raise BadRequestException(
                "The process cannot be run because it is not ready. Where the previous process run and are the inputs provided ?")

        try:
            return cls._create_cli(experiment, user, process_model)
        except Exception as err:
            traceback.print_exc()
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error(ProcessErrorInfo(detail=exception.get_detail_with_args(),
                                                      unique_code=exception.unique_code,
                                                      context=None, instance_id=exception.instance_id))
            raise exception

    @classmethod
    def _create_cli(cls, experiment: Experiment, user: User,
                    process_model: ProcessModel = None) -> SysProc:
        settings: Settings = Settings.get_instance()
        cwd_dir = settings.get_cwd()

        # set the user in the context to make the update works
        CurrentUserService.set_current_user(user)

        # check user privilege
        experiment.check_user_privilege(user)

        if experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the experiment {experiment.id}")

        if process_model and process_model.status == ProcessStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the process {process_model.id}")

        cmd = [
            "python3",
            os.path.join(cwd_dir, "manage.py"),
            "--run-experiment",
            "--experiment-id", experiment.id,
            "--user-id", user.id
        ]

        if process_model:
            cmd.extend([
                "--protocol-model-id", process_model.parent_protocol_id,
                "--process-instance-name", process_model.instance_name
            ])

        if settings.is_test:
            # add test option to tell the sub process is a test
            cmd.extend(["--test", "a"])

        sproc = SysProc.popen(
            cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        # Mark that a process is created for the experiment, but it is not started yet
        experiment.mark_as_waiting_for_cli_process(sproc.pid)

        if process_model:
            # Mark also the process as waiting for cli process
            process_model.mark_as_waiting_for_cli_process()

        Logger.info(
            f"Experiment process run_through_cli {str(cmd)}")
        Logger.info(
            f"""The experiment logs are not shown in the console, because it is run in another linux process ({experiment.pid}).
            To view them check the logs marked as {Logger.SUB_PROCESS_TEXT} in the today's log file : {Logger.get_file_path()}""")
        return sproc

    @classmethod
    def stop_experiment(cls, id: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_id_and_check(id)

        experiment.check_is_stopable()

        # try to kill the pid if possible
        try:
            if experiment.pid is not None:
                cls._kill_experiment_pid(experiment.pid)
        except Exception as err:
            Logger.error(str(err))

        # mark the experiment as error
        error = ProcessErrorInfo(
            detail=f"Experiment manually stopped by {CurrentUserService.get_and_check_current_user().full_name}",
            unique_code="EXPERIMENT_STOPPED_MANUALLY",
            context=None,
            instance_id=None
        )
        experiment.mark_as_error(error)

        # mark all the running tasks as error
        task_models: List[TaskModel] = experiment.get_running_tasks()
        for task_model in task_models:
            exception = ProcessRunException(task_model, error.detail,
                                            error.unique_code, "Task error", None)
            task_model.mark_as_error_and_parent(exception)

        ActivityService.add(
            ActivityType.STOP_EXPERIMENT,
            object_type=ActivityObjectType.EXPERIMENT,
            object_id=experiment.id
        )

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
            sproc.kill_with_children()
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
                Logger.error(
                    f'Could not stop experiment {experiment.id}. {str(err)}')

    @classmethod
    def get_all_running_experiments(cls) -> List[Experiment]:
        return list(
            Experiment.select().where(
                (Experiment.status == ExperimentStatus.RUNNING) |
                (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)))

    @classmethod
    def _send_experiment_finished_mail(cls, experiment: Experiment) -> None:
        if not Settings.get_instance().is_prod_mode() or not experiment.is_manual():
            return
        try:
            elapsed_time = experiment.protocol_model.progress_bar.get_last_execution_time()

            # if the last execution was runned in under 5 minutes, don't send an email
            if elapsed_time < 1000 * 60 * 5:
                return

            user: User = CurrentUserService.get_and_check_current_user()
            experiment_dto = SendExperimentFinishMailData(
                title=experiment.title,
                status=experiment.status.value,
                experiment_link=FrontService.get_experiment_url(experiment_id=experiment.id)
            )

            MailService.send_experiment_finished_mail(user.id, experiment_dto)
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            Logger.error(
                f"Error while sending the experiment finished mail : {err}")

import os
import subprocess
import traceback

from gws_core.core.service.front_service import FrontService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.monitor.monitor_service import MonitorService
from gws_core.process.process_exception import ProcessRunException
from gws_core.process.process_model import ProcessModel
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.space.mail_service import MailService
from gws_core.space.space_dto import SendScenarioFinishMailData
from gws_core.task.task_model import TaskModel
from gws_core.user.activity.activity_dto import ActivityObjectType, ActivityType

from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.sys_proc import SysProc
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..user.activity.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .scenario import Scenario
from .scenario_enums import ScenarioStatus
from .scenario_exception import ScenarioRunException


class ScenarioRunService:
    """Service used to run scenario"""

    # additional disk space required to run the scenario
    REQUIRED_DISK_SPACE_RUN_SCENARIO = 1 * 1024 * 1024 * 1024  # 1 GB

    @classmethod
    def run_scenario_in_cli(cls, scenario_id: str) -> None:
        """Method called by the cli sub process to run the scenario"""
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        if scenario.status != ScenarioStatus.WAITING_FOR_CLI_PROCESS:
            Logger.error(
                f"Cannot run the scenario {scenario.id} as its status was changed before process could run it"
            )
            scenario.mark_as_error(
                ProcessErrorInfo(
                    detail=f"Cannot run the scenario {scenario.id} as its status was changed before process could run it",
                    unique_code=GWSException.SCENARIO_ERROR_BEFORE_RUN.name,
                    context=None,
                    instance_id=None,
                )
            )
            return

        cls.run_scenario(scenario)

    @classmethod
    def run_scenario_by_id(cls, scenario_id: str) -> Scenario:
        """
        Run the scenario by ID.

        :param scenario_id: The ID of the scenario to run
        :type scenario_id: str
        """
        scenario = Scenario.get_by_id_and_check(scenario_id)
        return cls.run_scenario(scenario)

    @classmethod
    def run_scenario(cls, scenario: Scenario) -> Scenario:
        """
        Run the scenario
        """
        try:
            cls._check_scenario_before_start(scenario)

            scenario.mark_as_started(os.getpid())

            Logger.info(f"Running scenario : {scenario.id}")

            ActivityService.add(
                ActivityType.RUN_SCENARIO,
                object_type=ActivityObjectType.SCENARIO,
                object_id=scenario.id,
            )

            scenario.protocol_model.run()

            scenario = scenario.refresh()
            scenario.mark_as_success()

            cls._send_scenario_finished_mail(scenario)

            return scenario
        except Exception as err:
            exception: ScenarioRunException = ScenarioRunException.from_exception(
                scenario=scenario, exception=err
            )
            error = ProcessErrorInfo(
                detail=exception.get_detail_with_args(),
                unique_code=exception.unique_code,
                context=None,
                instance_id=exception.instance_id,
            )
            scenario = scenario.refresh()
            scenario.mark_as_error(error)

            cls._send_scenario_finished_mail(scenario)
            raise exception

    @classmethod
    def run_scenario_process_in_cli(
        cls, scenario_id: str, protocol_model_id: str, process_name: str
    ) -> None:
        """Method called by the cli sub process to run the scenario"""
        try:
            scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

            protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_model_id)

            process_model = protocol_model.get_process(process_name)

            if scenario.status != ScenarioStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the scenario {scenario.id} as its status was changed before process could run it"
                )

            if process_model.status != ProcessStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the process {process_model.id} as its status was changed before process could run it"
                )

        except Exception as err:
            error_text = GWSException.SCENARIO_ERROR_BEFORE_RUN.value + str(err)
            Logger.error(error_text)
            scenario.mark_as_error(
                ProcessErrorInfo(
                    detail=error_text,
                    unique_code=GWSException.SCENARIO_ERROR_BEFORE_RUN.name,
                    context=None,
                    instance_id=None,
                )
            )
        cls._run_scenario_process(scenario, protocol_model, process_name)

    @classmethod
    def _run_scenario_process(
        cls, scenario: Scenario, protocol_model: ProtocolModel, process_instance_name: str
    ) -> Scenario:
        try:
            process_model = protocol_model.get_process(process_instance_name)

            cls._check_scenario_before_start(scenario)

            if not protocol_model.process_is_ready(process_model):
                raise BadRequestException(
                    "The process cannot be run because it is not ready. Where the previous process run and are the inputs provided ?"
                )

            Logger.info(
                f"Running scenario process : {scenario.id}, protocol: {protocol_model.id}, process: {process_instance_name}"
            )

            ActivityService.add(
                ActivityType.RUN_PROCESS,
                object_type=ActivityObjectType.PROCESS,
                object_id=process_model.id,
            )

            scenario.mark_as_started(os.getpid())

            protocol_model.run_process(process_instance_name)
            protocol_model = protocol_model.refresh()
            protocol_model.refresh_status()
            return scenario

        except Exception as err:
            exception: ProcessRunException = ProcessRunException.from_exception(
                process_model=process_model, exception=err
            )

            process_model.mark_as_error_and_parent(exception)
            raise exception

    @classmethod
    def _check_scenario_before_start(cls, scenario: Scenario) -> None:
        # check scenario status
        scenario.check_is_runnable()

    @classmethod
    def create_cli_for_scenario(cls, scenario: Scenario, user: User) -> SysProc:
        """
        Run a scenario in a non-blocking way through the cli.

        :param user: The user who is running the scenario. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        try:
            return cls._create_cli(scenario, user)
        except Exception as err:
            traceback.print_exc()
            exception: ScenarioRunException = ScenarioRunException.from_exception(
                scenario=scenario, exception=err
            )
            scenario.mark_as_error(
                ProcessErrorInfo(
                    detail=exception.get_detail_with_args(),
                    unique_code=exception.unique_code,
                    context=None,
                    instance_id=exception.instance_id,
                )
            )
            raise exception

    @classmethod
    def create_cli_for_scenario_process(
        cls,
        scenario: Scenario,
        protocol_model: ProtocolModel,
        process_instance_name: str,
        user: User,
    ) -> SysProc:
        """
        Run a scenario in a non-blocking way through the cli.

        :param user: The user who is running the scenario. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        process_model = protocol_model.get_process(process_instance_name)

        if not protocol_model.process_is_ready(process_model):
            raise BadRequestException(
                "The process cannot be run because it is not ready. Where the previous process run and are the inputs provided ?"
            )

        # Autnenticate the user if necessary because it can be triggered by the queue so the user is not authenticated
        try:
            return cls._create_cli(scenario, user, process_model)
        except Exception as err:
            traceback.print_exc()
            exception: ScenarioRunException = ScenarioRunException.from_exception(
                scenario=scenario, exception=err
            )
            scenario.mark_as_error(
                ProcessErrorInfo(
                    detail=exception.get_detail_with_args(),
                    unique_code=exception.unique_code,
                    context=None,
                    instance_id=exception.instance_id,
                )
            )
            raise exception

    @classmethod
    def _create_cli(
        cls, scenario: Scenario, user: User, process_model: ProcessModel | None = None
    ) -> SysProc:
        if scenario.status == ScenarioStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the scenario {scenario.id}"
            )

        if process_model and process_model.status == ProcessStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the process {process_model.id}"
            )

        cls._check_disk_space_before_run(scenario)

        settings = Settings.get_instance()
        gws_core_path = settings.get_brick("gws_core").path

        options: list[str] = [
            "--scenario-id",
            scenario.id,
            "--user-id",
            user.id,
        ]

        if settings.is_test:
            options.append("--test")

        command: str
        if process_model:
            options.extend(
                [
                    "--protocol-model-id",
                    process_model.parent_protocol_id,
                    "--process-instance-name",
                    process_model.instance_name,
                ]
            )
            command = "run-process"

        else:
            command = "run-scenario"

        cmd = [
            "python3",
            os.path.join(gws_core_path, "gws_cli", "gws_cli", "main_cli.py"),
            "--log-level",
            Logger.level,
            "server",
            command,
        ] + options

        sproc = SysProc.popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        # Mark that a process is created for the scenario, but it is not started yet
        scenario.mark_as_waiting_for_cli_process(sproc.pid)

        if process_model:
            # Mark also the process as waiting for cli process
            process_model.mark_as_waiting_for_cli_process()

        Logger.info(f"Scenario process run_through_cli {str(cmd)}")
        Logger.info(
            f"""The scenario logs are not shown in the console, because it is run in another linux process ({scenario.pid}).
            To view them check the logs in the today's log file : {Logger.get_file_path()}"""
        )
        return sproc

    @classmethod
    def _check_disk_space_before_run(cls, scenario: Scenario) -> None:
        # check if there is enough disk space
        free_disk = MonitorService.get_free_disk_info()

        if not free_disk.has_enough_space_for_file(cls.REQUIRED_DISK_SPACE_RUN_SCENARIO):
            required_space_pretty = FileHelper.get_file_size_pretty_text(
                cls.REQUIRED_DISK_SPACE_RUN_SCENARIO + free_disk.required_disk_free_space
            )

            error = f"Not enough disk space to run the scenario. It requires at least {required_space_pretty} of free space"

            scenario.mark_as_error(ProcessErrorInfo(detail=error))
            raise BadRequestException(error)

    @classmethod
    def stop_scenario(cls, id: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id)

        scenario.check_is_stopable()

        # try to kill the pid if possible
        try:
            if scenario.pid is not None:
                cls._kill_scenario_pid(scenario.pid)
        except Exception as err:
            Logger.error(str(err))

        # mark the scenario as error
        error = ProcessErrorInfo(
            detail=f"Scenario manually stopped by {CurrentUserService.get_and_check_current_user().full_name}",
            unique_code="SCENARIO_STOPPED_MANUALLY",
            context=None,
            instance_id=None,
        )
        scenario.mark_as_error(error)

        # mark all the running tasks as error
        task_models: list[TaskModel] = scenario.get_running_tasks()
        for task_model in task_models:
            exception = ProcessRunException(
                task_model, error.detail, error.unique_code, "Task error", None
            )
            task_model.mark_as_error_and_parent(exception)

        ActivityService.add(
            ActivityType.STOP_SCENARIO,
            object_type=ActivityObjectType.SCENARIO,
            object_id=scenario.id,
        )

        return scenario

    @classmethod
    def _kill_scenario_pid(cls, scenario_pid: int) -> None:
        """
        Kill the scenario through HTTP context if it is running

        This is only possible if the scenario has been started through the cli
        """

        if not scenario_pid or scenario_pid == 0:
            raise BadRequestException(f"The scenario pid is {scenario_pid}")
        try:
            sproc = SysProc.from_pid(scenario_pid)
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {scenario_pid}). Error: {err}"
            ) from err

        # Don't kill if the process is already a zombie
        if sproc.is_zombie():
            return

        try:
            # Gracefully stops the scenario and exits!
            sproc.kill_with_children()
            sproc.wait()
        except Exception as err:
            raise BadRequestException(
                f"Cannot kill the scenario (pid = {scenario_pid}). Error: {err}"
            ) from err

    @classmethod
    def stop_all_running_scenario(cls) -> None:
        scenarios: list[Scenario] = cls.get_all_running_scenarios()
        for scenario in scenarios:
            try:
                cls.stop_scenario(scenario.id)
            except Exception as err:
                Logger.error(f"Could not stop scenario {scenario.id}. {str(err)}")

    @classmethod
    def get_all_running_scenarios(cls) -> list[Scenario]:
        return list(
            Scenario.select().where(
                (Scenario.status == ScenarioStatus.RUNNING)
                | (Scenario.status == ScenarioStatus.WAITING_FOR_CLI_PROCESS)
            )
        )

    @classmethod
    def _send_scenario_finished_mail(cls, scenario: Scenario) -> None:
        if not Settings.get_instance().is_prod_mode() or not scenario.is_manual():
            return
        try:
            elapsed_time = scenario.protocol_model.progress_bar.get_last_execution_time()

            # if the last execution was runned in under 5 minutes, don't send an email
            if elapsed_time < 1000 * 60 * 5:
                return

            user: User = CurrentUserService.get_and_check_current_user()
            scenario_dto = SendScenarioFinishMailData(
                title=scenario.title,
                status=scenario.status.value,
                scenario_link=FrontService.get_scenario_url(scenario_id=scenario.id),
            )

            MailService.send_scenario_finished_mail(user.id, scenario_dto)
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            Logger.error(f"Error while sending the scenario finished mail : {err}")

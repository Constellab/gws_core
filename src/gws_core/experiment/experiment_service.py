# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import traceback
from math import exp
from posix import listdir
from typing import Any, Coroutine, Dict, List, Type, Union

from gws_core.study.study_dto import StudyDto
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException, NotFoundException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.sys_proc import SysProc
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..experiment.experiment_exception import ExperimentRunException
from ..process.process_factory import ProcessFactory
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..study.study import Study
from ..study.study_service import StudyService
from ..task.task import Task
from ..task.task_model import TaskModel
from ..task.task_service import TaskService
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment, ExperimentStatus
from .experiment_dto import ExperimentDTO


class ExperimentService(BaseService):

    ################################### CREATE ##############################

    @classmethod
    def create_empty_experiment(cls, experimentDTO: ExperimentDTO) -> Experiment:

        # retrieve the study
        study: Study = StudyService.get_or_create_study_from_dto(experimentDTO.study)

        return cls.create_experiment_from_protocol_model(
            protocol_model=ProcessFactory.create_protocol_empty(),
            study=study,
            title=experimentDTO.title,
            description=experimentDTO.description
        )

    @classmethod
    @transaction()
    def create_experiment_from_task_model(
            cls, task_model: TaskModel, study: Study = None, title: str = "", description: str = "") -> Experiment:
        if not isinstance(task_model, TaskModel):
            raise BadRequestException("An instance of TaskModel is required")
        proto = ProtocolService.create_protocol_model_from_task_model(task_model=task_model)
        return cls.create_experiment_from_protocol_model(
            protocol_model=proto, study=study, title=title, description=description)

    @classmethod
    @transaction()
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, study: Study = None, title: str = "", description: str = "") -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException("An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.set_title(title)
        experiment.set_description(description)
        experiment.created_by = CurrentUserService.get_and_check_current_user()
        experiment.study = study

        experiment = experiment.save()

        # Set the experiment for the protocol_model and childs and save them
        protocol_model.set_experiment(experiment)
        protocol_model.save_full()
        return experiment

    @classmethod
    def create_experiment_from_protocol_type(
            cls, protocol_type: Type[Protocol],
            study: Study = None, title: str = "", description: str = "") -> Experiment:

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(protocol_type=protocol_type)
        return cls.create_experiment_from_protocol_model(
            protocol_model=protocol_model, study=study, title=title, description=description)

    @classmethod
    def create_experiment_from_task_type(
            cls, task_type: Type[Task],
            study: Study = None, title: str = "", description: str = "") -> Experiment:

        task_model: TaskModel = TaskService.create_task_model_from_type(task_type=task_type)
        return cls.create_experiment_from_task_model(
            task_model=task_model, study=study, title=title, description=description)

        # -- F --

    ################################### UPDATE ##############################

    @classmethod
    def update_experiment(cls, uri, experiment_DTO: ExperimentDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_uri_and_check(uri)

        experiment.check_is_updatable()

        experiment.set_title(experiment_DTO.title)
        experiment.set_description(experiment_DTO.description)
        experiment.study = StudyService.get_or_create_study_from_dto(experiment_DTO.study)

        experiment.save()
        return experiment

    @classmethod
    def update_experiment_protocol(cls, uri: str, protocol_graph: Dict) -> Experiment:
        experiment: Experiment = Experiment.get_by_uri_and_check(uri)

        experiment.check_is_updatable()
        ProtocolService.update_protocol_graph(protocol_model=experiment.protocol_model, graph=protocol_graph)

        experiment.save()
        return experiment

    @classmethod
    @transaction()
    def validate_experiment(cls, uri: str, study_dto: StudyDto = None) -> Experiment:
        experiment: Experiment = Experiment.get_by_uri_and_check(uri)

        # set the study if it is provided
        if study_dto is not None:
            experiment.study = StudyService.get_or_create_study_from_dto(study_dto)

        experiment.validate()

        user: User = CurrentUserService.get_and_check_current_user()
        ActivityService.add(Activity.VALIDATE_EXPERIMENT,
                            object_type=Experiment.full_classname(),
                            object_uri=experiment.uri,
                            user=user)

        return experiment

    ################################### GET  ##############################

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.count_of_running_experiments()

    @classmethod
    def get_experiment_by_uri(cls, uri: str) -> Experiment:
        return Experiment.get_by_uri_and_check(uri)

    @classmethod
    def fetch_experiment_list(cls,
                              page: int = 0,
                              number_of_items_per_page: int = 20) -> Paginator[Experiment]:

        number_of_items_per_page = cls.get_number_of_item_per_page(
            number_of_items_per_page)

        query = Experiment.select().order_by(Experiment.creation_datetime.desc())

        paginator: Paginator[Experiment] = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def search(cls,
               search_text: str,
               page: int = 0,
               number_of_items_per_page: int = 20,
               as_json: bool = False) -> Paginator:

        number_of_items_per_page = cls.get_number_of_item_per_page(
            number_of_items_per_page)

        query: ModelSelect = Experiment.search(search_text)
        result = []
        for o in query:
            if as_json:
                result.append(o.get_related().to_json())
            else:
                result.append(o.get_related())

        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        return {
            'data': result,
            'paginator': paginator._get_paginated_info()
        }

    @classmethod
    def get_all_running_experiments(cls) -> List[Experiment]:
        return list(
            Experiment.select().where(
                (Experiment.status == ExperimentStatus.RUNNING) |
                (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)))

    ################################### RUN ##############################

    @classmethod
    async def run_experiment_in_cli(cls, experiment_uri: str, user_uri: str) -> None:
        """Method called by the cli sub process to run the experiment
        """
        experiment: Experiment = Experiment.get_by_uri_and_check(experiment_uri)

        try:
            user: User = User.get_by_uri_and_check(user_uri)

            if not user.is_authenticated:
                raise BadRequestException("The user must be HTTP authenticated")

            if experiment.status != ExperimentStatus.WAITING_FOR_CLI_PROCESS:
                raise Exception(
                    f"Cannot run the experiment {experiment.uri} as it status was changed before process could run it")

        except Exception as err:
            error_text = GWSException.EXPERIMENT_ERROR_BEFORE_RUN.value + str(err)
            Logger.error(error_text)
            experiment.mark_as_error({"detail": error_text,
                                      "unique_code": GWSException.EXPERIMENT_ERROR_BEFORE_RUN.name,
                                      "context": None, "instance_id": None})
        await cls.run_experiment(experiment, user)

    @classmethod
    async def run_experiment(cls, experiment: Experiment, user: User = None) -> Coroutine[Any, Any, Experiment]:
        """
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """
        # check user
        if not user:
            try:
                user = CurrentUserService.get_and_check_current_user()
            except:
                raise BadRequestException("A user is required")

        # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

        Logger.info(f"Running experiment : {experiment.uri}")

        ActivityService.add(
            Activity.START,
            object_type=experiment.full_classname(),
            object_uri=experiment.uri,
            user=user
        )

        try:
            experiment.mark_as_started()

            await experiment.protocol_model.run()

            experiment.mark_as_success()

            return experiment
        except Exception as err:
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error({"detail": exception.get_detail_with_args(), "unique_code": exception.unique_code,
                                      "context": exception.context, "instance_id": exception.instance_id})
            raise exception

    @classmethod
    def create_cli_process_for_experiment(cls, experiment: Experiment, user=None):
        """
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        settings: Settings = Settings.retrieve()
        cwd_dir = settings.get_cwd()

        # check user
        if not user:
            try:
                user = CurrentUserService.get_and_check_current_user()
            except:
                raise BadRequestException("A user is required")
            if not user.is_authenticated:
                raise BadRequestException("An authenticated user is required")

         # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

        if experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS:
            raise BadRequestException(
                f"A CLI process was already created to run the experiment {experiment.uri}")

        cmd = [
            "python3",
            os.path.join(cwd_dir, "manage.py"),
            "--cli",
            "gws_core.cli.run_experiment",
            "--experiment-uri", experiment.uri,
            "--user-uri", user.uri
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
    def stop_experiment(cls, uri: str) -> Experiment:
        experiment: Experiment = Experiment.get_by_uri_and_check(uri)

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
            object_uri=experiment.urip
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
                cls.stop_experiment(experiment.uri)
            except Exception as err:
                Logger.error(f'Could not stop experiment {experiment.uri}. {str(err)}')

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import traceback
from typing import Any, Coroutine, Union

from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.experiment.experiment_exception import ExperimentRunException
from gws_core.processable.processable_factory import ProcessableFactory
from gws_core.protocol.protocol_service import ProtocolService
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException, NotFoundException
from ..core.model.sys_proc import SysProc
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..process.process_model import ProcessModel
from ..protocol.protocol_model import ProtocolModel
from ..study.study import Study
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment, ExperimentStatus
from .experiment_dto import ExperimentDTO


class ExperimentService(BaseService):

    # -- C --

    @classmethod
    def create_empty_experiment(cls, experimentDTO: ExperimentDTO) -> Experiment:
        return cls.create_experiment_from_protocol_model(
            protocol_model=ProcessableFactory.create_protocol_empty(),
            study=None,
            title=experimentDTO.title,
            description=experimentDTO.description
        )

    @classmethod
    def create_experiment_from_process_model(
            cls, process_model: ProcessModel, study: Study = None, title: str = "", description: str = "") -> Experiment:
        if not isinstance(process_model, ProcessModel):
            raise BadRequestException("An instance of ProcessModel is required")
        proto = ProtocolService.create_protocol_model_from_process_model(process_model=process_model)
        return cls.create_experiment_from_protocol_model(
            protocol_model=proto, study=study, title=title, description=description)

    @classmethod
    def create_experiment_from_protocol_model(
            cls, protocol_model: ProtocolModel, study: Study = None, title: str = "", description: str = "") -> Experiment:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException("An instance of ProtocolModel is required")
        experiment = Experiment()
        experiment.set_title(title)
        experiment.set_description(description)
        experiment.study = Study.get_default_instance() if study is None else study
        experiment.created_by = CurrentUserService.get_and_check_current_user()

        experiment = experiment.save()

        # Set the experiment for the protocol_model and childs and save them
        protocol_model.set_experiment(experiment)
        protocol_model.save_full()
        return experiment

    # -- F --

    @classmethod
    def get_experiment_by_uri(cls, uri: str) -> Union[Experiment, dict]:
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

    # -- S --

    @classmethod
    async def stop_experiment(cls, uri) -> Experiment:
        experiment: Experiment = None

        try:
            experiment = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise BadRequestException(
                detail=f"Experiment '{uri}' not found") from err

        experiment.check_is_stopable()

        try:
            cls._kill_experiment_pid(experiment)
            return experiment
        except Exception as err:
            raise BadRequestException(
                detail=f"Cannot kill experiment '{uri}'") from err

    @classmethod
    def _kill_experiment_pid(cls, experiment: Experiment) -> Experiment:
        """
        Kill the experiment through HTTP context if it is running

        This is only possible if the experiment has been started through the cli
        """

        # if not HTTPHelper.is_http_context():
        #    raise BadRequestException("The user must be in http context")

        if not experiment.pid:
            raise BadRequestException(
                f"The experiment pid is {experiment.pid}")
        try:
            sproc = SysProc.from_pid(experiment.pid)
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {experiment.pid}). Error: {err}") from err

        try:
            # Gracefully stops the experiment and exits!
            sproc.kill()
            sproc.wait()
        except Exception as err:
            raise BadRequestException(
                f"Cannot kill the experiment (pid = {experiment.pid}). Error: {err}") from err

        ActivityService.add(
            Activity.STOP,
            object_type=experiment.full_classname(),
            object_uri=experiment.uri
        )

        # todo uniquify unique name
        experiment.mark_as_error({"detail": GWSException.EXPERIMENT_STOPPED_MANUALLY.value,
                                  "unique_code": GWSException.EXPERIMENT_STOPPED_MANUALLY.name, "context": None})

    # -- U --

    @classmethod
    def update_experiment(cls, uri, experiment_DTO: ExperimentDTO) -> Experiment:
        experiment: Experiment = Experiment.get_by_uri_and_check(uri)

        experiment.check_is_updatable()

        if experiment_DTO.graph:
            ProtocolService.update_protocol_graph(protocol_model=experiment.protocol, graph=experiment_DTO.graph)

        if experiment_DTO.title:
            experiment.set_title(experiment_DTO.title)

        if experiment_DTO.description:
            experiment.set_description(experiment_DTO.description)

        experiment.save()
        return experiment

    # -- V --

    @classmethod
    def validate_experiment(cls, uri) -> Experiment:
        experiment: Experiment = None
        try:
            experiment = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise NotFoundException(
                detail=f"Experiment '{uri}' not found") from err

        try:
            experiment.validate(
                user=CurrentUserService.get_and_check_current_user())
            return experiment
        except Exception as err:
            raise NotFoundException(
                detail=f"Cannot validate experiment '{uri}'") from err

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

            await experiment.protocol.run()

            experiment.mark_as_success()

            return experiment
        except Exception as err:
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error({"detail": exception.get_detail_with_args(), "unique_code": exception.unique_code,
                                      "context": exception.context})
            raise exception

    @classmethod
    def run_through_cli(cls, experiment: Experiment, user=None):
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
            Logger.info(
                f"gws.experiment.Experiment run_through_cli {str(cmd)}")
            Logger.info(
                f"""The experiment logs are not shown in the console, because it is run in another linux process.
                To view them check the logs marked as {Logger.get_sub_process_text()} in the today's log file : {Logger.get_file_path()}""")
            sproc = SysProc.popen(
                cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # Mark that a process is created for the experiment, but it is not started yet
            experiment.mark_as_waiting_for_cli_process(sproc.pid)
        except Exception as err:
            traceback.print_exc()
            exception: ExperimentRunException = ExperimentRunException.from_exception(
                experiment=experiment, exception=err)
            experiment.mark_as_error({"detail": exception.get_detail_with_args(), "unique_code": exception.unique_code,
                                      "context": exception.context})
            raise exception

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.count_of_running_experiments()
